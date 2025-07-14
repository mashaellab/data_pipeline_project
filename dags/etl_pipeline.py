

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from faker import Faker
import pandas as pd
import os
import psycopg2

def generate_fake_data():
    fake = Faker()
    reasons = ['Complaint', 'Inquiry', 'Suggestion']
    channels = ['Email', 'Chat', 'Phone']
    data = []

    for i in range(100):
        data.append({
            'ticket_id': f"TCKT{i+1:04d}",
            'reason': fake.random_element(reasons),
            'channel': fake.random_element(channels),
            'rating': fake.random_int(min=1, max=5),
            'response_time': fake.random_int(min=1, max=60),
            'date': fake.date_between(start_date='-30d', end_date='today')
        })

    df = pd.DataFrame(data)
    os.makedirs('/opt/airflow/data', exist_ok=True)
    df.to_csv('/opt/airflow/data/customer_feedback.csv', index=False)


def clean_data():
    file_path = '/opt/airflow/data/customer_feedback.csv'
    df = pd.read_csv(file_path)
    df.dropna(inplace=True)  
    df['date'] = pd.to_datetime(df['date'])  

    df.to_csv(file_path, index=False)

def upload_to_postgres():
    
    df = pd.read_csv('/opt/airflow/data/customer_feedback.csv')

    conn = psycopg2.connect(
        host='host.docker.internal',
        dbname='feedback_db',
        user='postgres',
        password='1234',
        port=5432
    )

    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            ticket_id TEXT,
            reason TEXT,
            channel TEXT,
            rating INT,
            response_time INT,
            date DATE
        );
    """)

    conn.commit()
    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO feedback (ticket_id, reason, channel, rating, response_time, date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, tuple(row))

    conn.commit()
    cur.close()
    conn.close()
  

# DAG definition

default_args = {
    'start_date': datetime(2025, 7, 13),
}

with DAG(
    dag_id='generate_customer_feedback',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
) as dag:

 
    generate_task = PythonOperator(
        task_id='generate_fake_feedback_data',
        python_callable=generate_fake_data
    )

    clean_task = PythonOperator(
        task_id='clean_feedback_data',
        python_callable=clean_data
    )

    upload_task = PythonOperator(
        task_id='upload_to_postgres',
        python_callable=upload_to_postgres
    )

    generate_task >> clean_task >> upload_task