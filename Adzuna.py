import requests
import csv
import time
import pytz
from time import sleep
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tzlocal import get_localzone
# Record the start time

local_tz = get_localzone()
#cst_time = pytz.timezone('America/Chicago')

search_terms = [
    "Data Engineer",
    "Data scientist",
    "Data Analyst",
    "Business Analyst",
    "Software Engineer",
    "Golang developer",
    "Java developer",
    "C++ developer",
    "python developer",
    "full stack",
    "Front-End Engineer",
    "Back-End Engineer",
    "machine learning",
    "artificial intelligence",
    "DevOps Engineer",
    "Site Reliability Engineer",
    "Cloud Engineer",
    "AWS Engineer",
    "ETL engineer",
    "Hadoop developer"
]

def fetch_jobs(app_id, app_key, search_term, days_ago=1):
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": 50,
        "title_only": search_term,
        "where": "US",
        "max_days_old": days_ago,
        "sort_by": "date",
        "salary_min": 60000,
        "salary_include_unknown": 1,
        #"full_time": 1,
        #"contract": 1,
        "content-type": "application/json"
    }

    headers = {
        'Accept': 'application/json'
    }

    all_jobs = []
    page = 1

    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    while True:
        base_url = f"https://api.adzuna.com/v1/api/jobs/us/search/{page}"
        try:
            response = session.get(base_url, headers=headers, params=params)
            print(response.url)

            if response.status_code == 200:
                data = response.json()
                jobs = data.get("results", [])
                print(f"Found {len(jobs)} jobs on page {page}")

                if not jobs:
                    break

                all_jobs.extend(jobs)
                page += 1
                sleep(1)  # Respect API rate limits
            else:
                print(f"Error fetching data: Status code {response.status_code}")
                print(f"Response content: {response.text}")
                break
        except requests.exceptions.SSLError as e:
            print(f"SSL Error: {e}")
            break
        except requests.exceptions.RequestException as e:
            print(f"Request Exception: {e}")
            break

    return all_jobs

def save_to_csv(jobs, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['search_term', 'source_website', 'JobId', 'Company', 'Title', 'Description', 'job_type', 'EmploymentType', 'salary', 'PostedDate', 'ApplyUrl', 'is_available', 'City', 'State', 'Country']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for job in jobs:
            try:
                state = job.get('location', {}).get('area', 'N/A')[1],
                state = state[0]
            except IndexError:
                state = 'N/A'
            try:
                city = job.get('location', {}).get('area', 'N/A')[-1],
                city = city[0]
            except IndexError:
                city = 'N/A'

            writer.writerow({
                'search_term': job.get('search_term', 'N/A'),
                'source_website': 'Adzuna',
                'JobId': job.get('id', 'N/A'),
                'Company': job.get('company', 'N/A').get('display_name', 'N/A'),
                'Title': job.get('title', 'N/A'),
                'Description': job.get('description', 'N/A'),
                #'job_type': 'N/A',
                'EmploymentType': job.get('contract_type', 'N/A'),
                'salary': str(job.get('salary_max', 'N/A')),
                'PostedDate': job.get('created', 'N/A').split('T')[0],
                'ApplyUrl': job.get('redirect_url', 'N/A'),
                #'is_available': 'yes',
                'Country': job.get('location', {}).get('area', 'N/A')[0],
                'State': state,
                'City': city
                #'salary_min': job.get('salary_min', 'N/A'),




                #'contract_time': job.get('contract_time', 'N/A'),
            })

def main():
    
    app_id = "Enter your API ID"  #Enter your API ID in the double quotes provided by adzuna
    app_key = "Enter your API key" #Enter your API key in the double quotes provided by Adzuna

    all_jobs = []

    for term in search_terms:
        print(f"Fetching jobs for: {term}")
        jobs = fetch_jobs(app_id, app_key, term, days_ago=1)
        for job in jobs:
            job['search_term'] = term  # Add the search term to each job entry
        all_jobs.extend(jobs)
        print(f"Found {len(jobs)} jobs for {term}")

    print(f"Total jobs found: {len(all_jobs)}")

    end_time = datetime.now(local_tz).strftime("%m_%d_%Y_%I_%M_%S_%p_%Z")
    #end_time = datetime.now(cst_time).strftime("%m_%d_%Y_%I_%M_%S_%p_CST")
    csv_file_name = 'Adzuna' + "_" + end_time
    csv_filename = csv_file_name + '.csv'
    #csv_filename = "adzuna_jobs_last_24hours.csv"
    save_to_csv(all_jobs, csv_filename)
    print(f"All jobs saved to {csv_filename}")

if __name__ == "__main__":
    main()
