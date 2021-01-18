import streamlit as st
import pandas as pd
import base64

st.title("PO Analysis")


def get_table_download_link(df, file_name):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv()
    # some strings <-> bytes conversions necessary here
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{file_name}">Download {file_name}</a>'
    return href


def process(purchase, order):
    # Construct the Vlookup column
    # The lookup column is by combining the fc_id_dv_id_distributor_name

    order["lookup_index"] = (
        order["fc_id"].astype(str)
        + "_"
        + order["drug_variation_id"].astype(str)
        + "_"
        + order["distributor_name"].astype(str)
    )

    purchase["lookup_index"] = (
        purchase["fc_id"].astype(str)
        + "_"
        + purchase["drug_variation_id"].astype(str)
        + "_"
        + purchase["distributor_name"].astype(str)
    )

    # Drop duplicates based on the lookup_index of order data
    order = order.drop_duplicates(subset=["lookup_index"])

    # In purchase, pull in the order loose quantity via the lookup column
    purchase = purchase.merge(
        order[["loose_quantity", "lookup_index"]],
        how="left",
        on="lookup_index",
        suffixes=(None, "_ordered"),
    )

    # Replace NaN with 0 and set the analysis column value to 'Not ordered'
    # We do this first by duplicating the loose_quantity_y column to a new column called analysis and then updating the NaN values
    purchase["analysis"] = purchase["loose_quantity_ordered"]
    purchase["loose_quantity_ordered"] = purchase["loose_quantity_ordered"].fillna(0)
    purchase["analysis"] = purchase["analysis"].fillna("Not ordered")

    # Set the excess, shortage and exact values for the rest of the analysis columns
    purchase["analysis"].loc[
        (purchase["analysis"] != "Not ordered")
        & (purchase["loose_quantity"] > purchase["loose_quantity_ordered"])
    ] = "Excess"
    purchase["analysis"].loc[
        (purchase["analysis"] != "Not ordered")
        & (purchase["loose_quantity"] < purchase["loose_quantity_ordered"])
    ] = "Shortage"
    purchase["analysis"].loc[
        (purchase["analysis"] != "Not ordered")
        & (purchase["loose_quantity"] == purchase["loose_quantity_ordered"])
    ] = "Equal"

    # Do a pivot
    pivot = pd.pivot_table(
        purchase,
        index=["distributor_name"],
        columns=["analysis"],
        values="loose_quantity",
        aggfunc="count",
    )

    st.text("Processing complete!")
    st.text("Output:")
    st.write(pivot)

    # Output the files
    st.markdown(get_table_download_link(purchase, "output.csv"), unsafe_allow_html=True)
    st.markdown(get_table_download_link(pivot, "pivot.csv"), unsafe_allow_html=True)


def main():
    order_file = st.file_uploader("Upload Order File", type=["csv"])
    if order_file:
        order = pd.read_csv(order_file)
        st.write(order.head())

    purchase_file = st.file_uploader("Upload Purchase File", type=["csv"])
    if purchase_file:
        purchase = pd.read_csv(purchase_file)
        st.write(purchase.head())

    if st.button("Process"):
        if purchase_file and order_file:
            process(purchase, order)
        else:
            st.write("Choose and purchase file and order file!")


if __name__ == "__main__":
    main()