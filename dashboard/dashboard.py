import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
sns.set_theme(style='dark')

# read all csv
def main_preprocessing():
    customer = pd.read_csv('data/customers_dataset.csv')
    order_item = pd.read_csv('data/order_items_dataset.csv')
    order_reviews = pd.read_csv('data/order_reviews_dataset.csv')
    order = pd.read_csv('data/orders_dataset.csv')
    products = pd.read_csv('data/products_dataset.csv')
    



    # merge all data
    # CUSTOMER - ORDER - ORDER_ITEM - PRODUCTS - REVIEWS
    all = pd.merge(customer, order, on='customer_id', how='inner')
    all = pd.merge(all, order_item, on='order_id', how='inner')
    all = pd.merge(all, products, on='product_id')

    # menggunakan left untuk mengambil reviews yang ada customernya saja
    all = pd.merge(all, order_reviews, on='order_id', how='left')

    # mengambil kolom tertentu saja
    selected_column_data = all[['customer_id', 'order_id', 'product_id', 'review_id', 'seller_id', 'review_score', 'product_category_name', 'order_status', 'order_purchase_timestamp']]

    return selected_column_data

def preprocessing_pertama(selected_column_data):
    cleaned_data = selected_column_data.dropna(axis=0, subset=['review_score']).drop_duplicates().reset_index(drop=True)
    product_category_score = cleaned_data.groupby('product_category_name')['review_score'].mean().sort_values(ascending=False)
    return product_category_score

def preprocesseing_kedua(selected_column_data):
    sellers = pd.read_csv('data/sellers_dataset.csv')
    selected_column_data = pd.merge(selected_column_data, sellers, on='seller_id', how='inner')
    finished_transaction = selected_column_data[(selected_column_data.order_status != 'canceled') & (selected_column_data.order_status != 'unavailable')]
    finished_transaction = finished_transaction[
    (finished_transaction.order_purchase_timestamp > '2018-01-01 00:00:00') &
        (finished_transaction.order_purchase_timestamp < '2018-12-31 23:59:59')
    ]

    finished_transaction.seller_id.value_counts()
    top_finished = finished_transaction.seller_id.value_counts()[:3].index.tolist()

    finished_transaction = finished_transaction[
    (finished_transaction.seller_id == top_finished[0]) |
        (finished_transaction.seller_id == top_finished[1]) |
                (finished_transaction.seller_id == top_finished[2])  
    ]


    # Convert the timestamp to datetime
    finished_transaction['timestamp'] = pd.to_datetime(finished_transaction['order_purchase_timestamp'])
    # Extract year-month from timestamp
    finished_transaction['year_month'] = finished_transaction['timestamp'].dt.to_period('M')
    # Group by seller_id and year_month, and count transactions
    transaction_counts = finished_transaction.groupby(['seller_id', 'year_month']).size().reset_index(name='transaction_count')
    transaction_counts['year_month'] = transaction_counts['year_month'].dt.to_timestamp()

    return transaction_counts

def optional(selected_column_data):
    order_payment = pd.read_csv('data/order_payments_dataset.csv')
    new_all = pd.merge(selected_column_data, order_payment, on='order_id', how='inner')
    payment_method = new_all.groupby('payment_type').size()
    payment_method = pd.DataFrame(payment_method.to_dict().items(), columns=['product_category_name','avg_review_score'])
    return payment_method

selected_column_data = main_preprocessing()
product_category_score = preprocessing_pertama(selected_column_data)
transaction_counts = preprocesseing_kedua(selected_column_data)
payment_method = optional(selected_column_data)


def first_visualization(product_category_score):
    product_category = pd.read_csv('data/product_category_name_translation.csv')
    product_category_score = pd.DataFrame(product_category_score.to_dict().items(), columns=['product_category_name','avg_review_score'])
    translated_category_score = pd.merge(product_category_score, product_category, on='product_category_name', how='inner')


    st.subheader("Best & Worst Performing Product")

    fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(50, 20))

    sns.barplot(x="product_category_name_english", y="avg_review_score", data=translated_category_score[:5], palette=['yellowgreen', 'grey', 'grey', 'grey', 'grey'], ax=ax[0])
    ax[0].set_ylabel(None)
    ax[0].set_title("The Highest Review Score of Product Category Name", loc="center", fontsize=50)
    ax[0].tick_params(axis='y', labelsize=35)
    ax[0].tick_params(axis='x', labelsize=30)
    ax[0].set_xticklabels(translated_category_score[:5].product_category_name_english, rotation=90)
    ax[0].set_xlabel(None)


    sns.barplot(x="product_category_name_english", y="avg_review_score", data=translated_category_score[-5:], palette=['grey', 'grey', 'grey', 'grey', 'indianred'], ax=ax[1])
    ax[1].set_ylabel(None)
    ax[1].set_title("The Lowest Review Score of Product Category Name", loc="center", fontsize=50)
    ax[1].tick_params(axis='y', labelsize=35)
    ax[1].tick_params(axis='x', labelsize=30)
    ax[1].set_xticklabels(translated_category_score[:5].product_category_name_english, rotation=90)
    ax[1].set_xlabel(None)

    st.pyplot(fig)

def second_visalization(transaction_counts):
    st.subheader("Transaction")
    
    fig, ax = plt.subplots(figsize=(20, 10))

    for seller in transaction_counts['seller_id'].unique():
        seller_data = transaction_counts[transaction_counts['seller_id'] == seller]
        sns.lineplot(
            x="year_month", 
            y="transaction_count",
            data=seller_data,
            ax=ax
        )
    ax.set_title("Monthly Transaction Counts by Seller", loc="center", fontsize=30)
    ax.set_ylabel('Transaction Count')
    ax.set_xlabel('Month')
    ax.tick_params(axis='y', labelsize=20)
    ax.tick_params(axis='x', labelsize=15)
    st.pyplot(fig)

def optional_visualization(payment_method):
    st.subheader("Payments")
    fig, ax = plt.subplots(figsize=(20, 10))

    sns.barplot(x='product_category_name', y='avg_review_score', data=payment_method, palette=['grey', 'yellowgreen', 'grey', 'grey'])
    ax.set_title("Payment method frequency", loc="center", fontsize=30)
    ax.set_ylabel('Transaction Count')
    ax.set_xlabel('Payment Method')

    st.pyplot(fig)


# STREAMLIT CODE
st.header('My E-Commerce Dashboard')

col1, col2 = st.columns(2)

with col1:
    total_orders = selected_column_data.__len__()
    st.metric("Total Orders", value=total_orders)

with col2:
    total_customers = selected_column_data.customer_id.unique().__len__()
    st.metric("Total Customers", value=total_customers)
first_visualization(product_category_score)
second_visalization(transaction_counts)
optional_visualization(payment_method)

st.caption('Copyright (c) Ekplorasi Data 2023')
