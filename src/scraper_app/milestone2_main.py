import pandas as pd
from bs4 import BeautifulSoup
import requests
from datetime import datetime


def scrape_sitemap(url):
    """
    Extracts all the links from a company's sitemap.xml.
    
    Args:
    url (str): The URL for a company sitemap.xml.
    
    Returns:
    pd.Series: A pandas Series with all the links, or None if no links found.
    """
    try:
        with requests.get(url) as response:
            response.raise_for_status()  # Check if the request was successful
            soup = BeautifulSoup(response.text, 'lxml-xml')
            urls = [link.text.strip() for link in soup.find_all('loc') if link]
            
            if not urls:
                return None  # Return None if no URLs found
            
            extended_urls = []
            for link in urls:
                if link.endswith('xml'):
                    try:
                        with requests.get(link) as response:
                            response.raise_for_status()  # Check if the request was successful
                            nested_soup = BeautifulSoup(response.text, 'lxml')
                            nested_urls = [url.text.strip() for url in nested_soup.find_all('loc') if url]
                            extended_urls.extend(nested_urls)
                    except requests.RequestException as e:
                        print(f"Error occurred while processing {link}: {e}")
                else:
                    extended_urls.append(link)
            
            if not extended_urls:
                return None  # Return None if no extended URLs found
            
            return pd.Series(extended_urls).drop_duplicates().str.strip()
    
    except requests.RequestException as e:
        print(f"Error occurred: {e}")
        return None  # Return None if the initial request fails

def scrape_website(all_links):
    """
    Extracts all the text data from the webpages of a company.
    
    Args:
    all_links (pd.Series): A pandas Series with all the links in the company's website.
    
    Returns:
    pd.DataFrame: A pandas DataFrame with the columns 'key' (webpage link), 'text' (includes 
                  the text of the webpage), and 'timestamp' (when the data was scraped).
    """

    text_dict = {}

    for link in all_links.to_list():
        try:
            with requests.get(link) as response:
                response.raise_for_status()
                print(link)
                
                soup = BeautifulSoup(response.text, 'lxml')
                [tag.decompose() for tag in soup.find_all(['header', 'nav', 'footer'])]
                
                text_only = soup.get_text(separator=' ', strip=True)
                text_dict[link] = text_only
        except requests.RequestException as e:
            print(f"Error occurred while processing {link}: {e}")
        
    if not text_dict:
        return pd.DataFrame()  # return empty DataFrame if no text is extracted

    df = pd.DataFrame(list(text_dict.items()), columns=['key', 'text'])
    df['timestamp'] = pd.to_datetime(datetime.today().date())
    
    return df

import pandas as pd

def main():
    """
    Runs the scraping engine, extracts data from the specified sitemaps, and saves
    the extracted data to a CSV file.
    
    The CSV file contains the scraped data from the first 10 webpages of each sitemap.
    """
    
    try:
        sitemap_df = pd.read_csv("sitemap.csv")
    except FileNotFoundError:
        print("Error: The file 'sitemap.csv' was not found.")
        return
    except pd.errors.EmptyDataError:
        print("Error: The file 'sitemap.csv' is empty.")
        return

    if 'sitemap' not in sitemap_df.columns:
        print("Error: The expected 'sitemap' column is missing in 'sitemap.csv'.")
        return

    print("Starting scraping:\n")
    for index, item in enumerate(sitemap_df['sitemap'], start=1):
        print(f"Working on {item} ...")
        links = scrape_sitemap(item)
        if links is None or links.empty:
            print(f"No links were found in {item}.\n")
            continue

        print(f"{links.shape[0]} webpages found for scraping. For demo, scraping only the first 10 webpages.\n")
        
        scraped_df = scrape_website(links[:10])
        if scraped_df.empty:
            print(f"No data was scraped from the first 10 links of {item}.\n")
            continue
            
        output_file = f'scraped_data_{index}.csv'
        scraped_df.to_csv(output_file, index=False)
        print(f"Finished scraping. Data stored in {output_file}\n")


if __name__ == "__main__":
    main()
