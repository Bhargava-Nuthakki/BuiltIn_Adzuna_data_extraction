import pytz
import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import pytz
from time import sleep
import urllib.parse
from datetime import datetime, timedelta

from tzlocal import get_localzone
# Record the start time
local_tz = get_localzone()
#cst_time = pytz.timezone('America/Chicago')

start_time = datetime.now()

def fetch_jobs(url, params):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.content
    else:
        print(f"Failed to fetch data: Status code {response.status_code}")
        return None

def parse_relative_time(time_str):
    current_time = datetime.now()
    if 'minutes' in time_str.lower() or 'hours' in time_str.lower():
        if 'minutes' in time_str.lower():
            minutes = int(time_str.split()[0])
            return current_time - timedelta(minutes=minutes)
        else:
            hours = int(time_str.split()[0])
            return current_time - timedelta(hours=hours)
    elif 'hour' in time_str.lower():
        return current_time - timedelta(hours=1)
    elif 'yesterday' in time_str.lower():
        return current_time - timedelta(days=1)
    elif 'day' in time_str.lower():
        days = int(time_str.split()[0])
        return current_time - timedelta(days=days)
    else:
        return current_time  # Default to current time if unable to parse


def parse_jobs(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    print(soup)

    print('Following is the info of Individual jobs printed and all of its info on html page')

    jobs = []
    job_listings = soup.find_all('div', attrs={'data-id': 'job-card'})

    separated_listings = []
    for job in job_listings:
        separated_listings.append(job.prettify())
    separated_jobs = '\n\n===================================================================================\n\n'.join(separated_listings)
    print(separated_jobs)

    print(f"Found {len(job_listings)} job listings")

    for index, job in enumerate(job_listings, 1):
        try:
            print(f"\nParsing job {index}:")

            title = job.find('h2', class_='fw-extrabold').find('a').text.strip()
            print(f"Title: {title}")

            company = job.find('div', attrs={'data-id': 'company-title'}).find('span').text.strip()

            print(f"Company: {company}")

            # Extract posted time
            posted_time = 'N/A'
            actual_posted_time = None
            location = 'N/A'
            country = 'US'
            city = 'N/A'
            state = 'N/A'
            salary = 'N/A'
            experience = 'N/A'
            location_divs = job.find_all('div', class_='d-flex align-items-start gap-sm')
            for div in location_divs:
                clock_icon = div.find('i', class_='fa-regular fa-clock fs-xs text-pretty-blue')
                location_icon = div.find('i', class_='fa-regular fa-location-dot fs-xs text-pretty-blue')
                salary_icon = div.find('i', class_='fa-regular fa-sack-dollar fs-xs text-pretty-blue')
                experience_icon = div.find('i', class_='fa-regular fa-trophy fs-xs text-pretty-blue')
                if clock_icon:
                    time_span = div.find('span', class_='font-barlow text-gray-03')
                    if time_span:
                        posted_time = time_span.text.strip()
                        actual_posted_time = parse_relative_time(posted_time)
                elif location_icon:
                    location_span = div.find('span', class_='font-barlow text-gray-03')
                    if location_span:
                        location = location_span.text.strip()
                        loc_split = location.split(',')
                        if len(loc_split) == 1:
                            if 'USA' in loc_split.lower() or 'India' in loc_split.lower():
                                country = loc_split[0]
                            else:
                                city = loc_split[0]
                        elif len(loc_split) == 2:
                            city = loc_split[0]
                            state = loc_split[-1]
                        else:
                            state = loc_split[0]
                elif salary_icon:
                    salary_span = div.find('span', class_='font-barlow text-gray-03')
                    if salary_span:
                        salary = salary_span.text.strip()
                elif experience_icon:
                    experience_span = div.find('span', class_='font-barlow text-gray-03')
                    if experience_span:
                        experience = experience_span.text.strip()
                else:
                    pass

            print(f"Posted: {posted_time}")
            print(f"Location: {location}")
            print(f"Salary: {salary}")
            print(f"Experience: {experience}")

            # Extract job type (Remote/Hybrid)
            job_type = []
            job_type_divs = job.find_all('div', class_='d-flex align-items-start gap-sm')
            for div in job_type_divs:
                type_span = div.find('span', class_='font-barlow text-gray-03')
                if type_span and type_span.text.strip() in ['Remote', 'Hybrid']:
                    job_type.append(type_span.text.strip())
            job_type = ', '.join(job_type) if job_type else 'InPerson'
            print(f"Job Type: {job_type}")

            job_link = 'https://builtin.com' + job.find('h2', class_='fw-extrabold').find('a')['href']
            print(f"Link: {job_link}")

            Job_Id ='N/A'
            Job_Id = job_link.split('/')[-1]

            domain = 'N/A'
            domain_div = job.find('div', class_='font-barlow fw-medium mb-md')
            if domain_div:
                domain = domain_div.text.strip()
            print(f"Industry Categories: {domain}")

            job_description = 'N/A'
            description_div = job.find('div', class_='fs-xs fw-regular mb-md')
            if description_div:
                job_description = description_div.text.strip()
            print(f"Job Description: {job_description}")

            jobs.append({
                'source_website': 'BuiltIn',
                'Title': title,
                'JobId': Job_Id,
                'Company': company,
                #'posted_time': posted_time,
                'PostedDate': actual_posted_time.strftime("%Y-%m-%d") if actual_posted_time else 'N/A',
                #'location': location,
                'Country': country,
                'City': city,
                'State': state,
                'job_type': job_type,
                'salary': salary,
                'experience': experience,
                'ApplyUrl': job_link,
                'domain': domain,
                'Description': job_description,
                #'IsAvailable': 'yes',
                #'EmploymentType' : 'N/A'
            })
        except Exception as e:
            print(f"Error parsing job {index}: {e}")
            print("HTML content of the job card:")
            print(job.prettify())
            continue

    return jobs, soup


def has_next_page(soup):
    pagination = soup.find('div', id='pagination')
    if pagination:
        next_button = pagination.find('a', attrs={'aria-label': 'Go to Next Page'})
        return next_button is not None
    return False


def get_next_page_url(soup, base_url):
    pagination = soup.find('div', id='pagination')
    if pagination:
        next_button = pagination.find('a', attrs={'aria-label': 'Go to Next Page'})
        if next_button and 'href' in next_button.attrs:
            return urllib.parse.urljoin(base_url, next_button['href'])
    return None


def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_to_csv(data, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['search_term', 'source_website', 'JobId', 'Company', 'Title', 'Description', 'job_type', 'experience', 'domain', 'salary', 'PostedDate', 'ApplyUrl', 'City', 'State', 'Country'])
        writer.writeheader()
        for search_term, jobs in data.items():
            for job in jobs:
                row = {'search_term': search_term, **job}
                writer.writerow(row)


def main():
    base_url = 'https://builtin.com/jobs'
    all_results = {}

    # List of search parameters
    search_params = [
        {"search": "Data Engineer", "daysSinceUpdated": "1", "country": "USA"},
        {"search": "Data Scientist", "daysSinceUpdated": "1", "country": "USA"},
        {"search": "Data Analyst", "daysSinceUpdated": "1", "country": "USA"},
        {"search": "Business Analyst", "daysSinceUpdated": "1", "country": "USA"},
        {"search": "Software Engineer", "daysSinceUpdated": "1", "country": "USA"},
        {"search": "Golang developer", "daysSinceUpdated": "1", "country": "USA"},
        {"search": "Java developer", "daysSinceUpdated": "1", "country": "USA"},
        {"search": "C++ developer", "daysSinceUpdated": "1", "country": "USA"},
        {"search": "python developer", "daysSinceUpdated": "1", "country": "USA"},
        {"search": "Full stack", "daysSinceUpdated": "1", "country": "USA"},
        {"search": "Front-End Engineer", "daysSinceUpdated": "1", "country": "USA"},
        {"search": "Back-End Engineer", "daysSinceUpdated": "1", "country": "USA"},
        {"search": "Machine learning", "daysSinceUpdated": "1", "country": "USA"},
        {"search": "Artificial Intelligence", "daysSinceUpdated": "1", "country": "USA"},
        {"search": "DevOps Engineer", "daysSinceUpdated": "1", "country": "USA"},
        {"search": "Site Reliability Engineer", "daysSinceUpdated": "1", "country": "USA"},
        {"search": "Cloud Engineer", "daysSinceUpdated": "1", "country": "USA"},
        {"search": "AWS Engineer", "daysSinceUpdated": "1", "country": "USA"},
        {"search": "ETL engineer", "daysSinceUpdated": "1", "country": "USA"},
        {"search": "Hadoop developer", "daysSinceUpdated": "1", "country": "USA"}
    ]

    length_of_search_params = 0

    for params in search_params:

        length_of_search_params += 1

        search_term = params['search']
        print(f"\nSearching for: {search_term}")

        all_jobs = []
        page = 1
        while True:
            params['page'] = str(page)
            print(f'Fetching data from page {page}...')

            html_content = fetch_jobs(base_url, params)

            if html_content:
                print(f"Received HTML content (length: {len(html_content)})")
                try:
                    jobs, soup = parse_jobs(html_content)
                    all_jobs.extend(jobs)
                    print(f"Fetched {len(jobs)} jobs from page {page}")

                    if not has_next_page(soup):
                        print("Reached last page")
                        break

                    page += 1
                except Exception as e:
                    print(f"Error processing page {page}: {e}")
                    break
            else:
                print(f"No data fetched for page {page}")
                break

            sleep(2)  # Be respectful to the server

        all_results[search_term] = all_jobs
        print(f'Fetched total of {len(all_jobs)} jobs for {search_term}')

    # Save results to JSON file
    json_filename = 'builtin_all_jobs.json'
    save_to_json(all_results, json_filename)
    print(f'All job results saved to {json_filename}')

    # Save results to CSV file
    if length_of_search_params == len(search_params):
        #end_time = str(datetime.now())
        #end_time = datetime.now(cst_time).strftime("%m_%d_%Y_%I_%M_%S_%p_CST")
        end_time = datetime.now(local_tz).strftime("%m_%d_%Y_%I_%M_%S_%p_%Z")
        csv_file_name = 'BuiltIn' + "_" + end_time
        csv_filename = csv_file_name + '.csv'
        save_to_csv(all_results, csv_filename)
        print(f'All job results saved to {csv_filename}')


if __name__ == '__main__':
    main()
