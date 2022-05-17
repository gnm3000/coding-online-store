import os
from dotenv import load_dotenv
import pandas as pd
import requests


load_dotenv()

BASEURL_SALES_SERVICE = os.getenv('BASEURL_SALES_SERVICE','http://localhost:8000')
BASEURL_CUSTOMER_SERVICE = os.getenv('BASEURL_CUSTOMER_SERVICE','http://localhost:5678')
BASEURL_SHIPPING_SERVICE = os.getenv('BASEURL_SHIPPING_SERVICE','http://localhost:5679')


class ReportGenerator:
    def run(self):

        customers = BASEURL_CUSTOMER_SERVICE+"/customers"

        shipping = BASEURL_SHIPPING_SERVICE+"/shipping/orders"

        products = BASEURL_SALES_SERVICE+"/sales/products"

        carts_checkout_list = BASEURL_SALES_SERVICE+"/sales/checkout/list"

        json_customers = requests.get(customers).json()

        df_customers = pd.read_json(customers)
        customers_who_paid = df_customers[~df_customers.purchase_history.isnull(
        )]

        wallet_from_to_by_customer = pd.json_normalize(
            json_customers,
            record_path="purchase_history",
            meta=[
                "_id",
                "full_name",
                "wallet_usd"]).groupby(
            [
                "_id",
                "full_name"]).agg(
                    {
                        "from_wallet": "first",
                        "to_wallet": "last"})
        wallet_from_to_by_customer

        df_carts = pd.read_json(carts_checkout_list)
        df_carts

        df_summary = wallet_from_to_by_customer.reset_index().set_index(
            "_id").join(df_carts.set_index("customer_id")[["status", "products"]])
        df_summary.index.name = "customer_id"
        df_summary  # here we need format product and add column shipping info

        product_list = pd.json_normalize(df_summary["products"]).T.apply(
            lambda x: ",".join([row["name"] for row in x if not row is None])).tolist()
        df_summary["products"] = product_list
        df_summary
        df_shipping = pd.read_json(shipping)

        json_shipping = requests.get(shipping).json()

        stages_orders = pd.json_normalize(
            json_shipping, record_path="status_history", meta=[
                "_id", "customer_id"])
        stages_orders

        stages_orders["created_at"] = pd.to_datetime(
            stages_orders["created_at"])
        stages_orders = stages_orders.sort_values(by=["_id", "created_at"])
        stages_orders

        stages_orders["time"] = stages_orders.created_at - \
            stages_orders.created_at.shift(1)
        stages_orders["time"] = stages_orders.time.shift(-1)
        stats_global_by_status = stages_orders.groupby(
            "status").agg({'time': ['mean', 'min', 'max']})
        stats_global_by_status = stats_global_by_status.drop("delivered")
        stats_global_by_status.columns = [
            "mean_hours", "min_hours", "max_hours"]
        stats_global_by_status["mean_hours"] = stats_global_by_status["mean_hours"].apply(
            lambda x: round(x.total_seconds() / 60 / 60, 2))
        stats_global_by_status["min_hours"] = stats_global_by_status["min_hours"].apply(
            lambda x: round(x.total_seconds() / 60 / 60, 2))
        stats_global_by_status["max_hours"] = stats_global_by_status["max_hours"].apply(
            lambda x: round(x.total_seconds() / 60 / 60, 2))
        stats_global_by_status  # This pass to json o csv
        print(stats_global_by_status)
        stages_orders_si = stages_orders.copy()

        stages_orders_si = stages_orders_si[stages_orders_si.status != "delivered"]
        stages_orders_si["label"] = stages_orders_si["status"] + \
            ' = ' + stages_orders_si["time"].astype(str)
        stages_orders_si

        shipping_info = stages_orders_si.groupby(
            "customer_id").agg({"label": ';'.join})
        shipping_info

        df_summary["shipping_info"] = shipping_info

        print(df_summary)  # this is for a dashboard
        return stats_global_by_status, df_summary
