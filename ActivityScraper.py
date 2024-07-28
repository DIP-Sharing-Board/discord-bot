import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.signalmanager import dispatcher
from pythainlp.util import normalize
import json
from typing import Dict
from urllib.parse import quote
import httpx
import jmespath
from langdetect import detect, DetectorFactory
import dateparser

class ActivityScraper:
    INSTAGRAM_APP_ID = ""  # Instagram app ID for accessing the Instagram API

    def __init__(self):
        DetectorFactory.seed = 0  # Setting a seed for language detection to ensure consistent results

    def get_deadline(self, url):
        response = requests.get(url)  # Send a GET request to the provided URL
        soup = BeautifulSoup(response.content, 'html.parser')  # Parse the HTML content using BeautifulSoup
        date_pattern = r'(\d{1,2}\s+\w+\s+\d{4})'  # Regex pattern to match date formats
        for h4 in soup.find_all('h4'):  # Iterate over all <h4> elements in the page
            text = h4.get_text(strip=True)  # Get the text content of the <h4> element
            match = re.search(date_pattern, text)  # Search for date pattern in the text
            if match:
                date_text = match.group(0)  # Extract the matched date text
                thai_months = {  # Mapping of Thai months to their corresponding numbers
                    'มกราคม': 1, 'กุมภาพันธ์': 2, 'มีนาคม': 3, 'เมษายน': 4,
                    'พฤษภาคม': 5, 'มิถุนายน': 6, 'กรกฎาคม': 7, 'สิงหาคม': 8,
                    'กันยายน': 9, 'ตุลาคม': 10, 'พฤศจิกายน': 11, 'ธันวาคม': 12
                }
                day, month_thai, year = date_text.split()  # Split the date text into day, month, and year
                month = thai_months.get(month_thai)  # Get the month number from the Thai month name
                if month:
                    year = int(year) - 543  # Convert Thai year to Gregorian year
                    try:
                        deadline = datetime(year, month, int(day))  # Create a datetime object for the deadline
                        return deadline  # Return the deadline
                    except ValueError:
                        print("Failed to create datetime object")  # Print error message if datetime creation fails
        print("Deadline not found or could not be parsed")  # Print message if no deadline is found
        return None  # Return None if no deadline is found

    class EventSpider(scrapy.Spider):
        name = 'event_spider'  # Name of the spider

        def __init__(self, start_urls, *args, **kwargs):
            super().__init__(*args, **kwargs)  # Initialize the spider with provided arguments
            self.start_urls = start_urls  # Set the start URLs for the spider

        def parse(self, response):
            domain = response.url.split('/')[2]  # Extract the domain from the URL
            if 'camphub.in.th' in domain:
                return self.parse_camphub(response)  # Parse the response using Camphub-specific method
            else:
                return self.parse_other(response)  # Parse the response using general method

        def parse_camphub(self, response):
            return {
                'topic': self.extract_topic(response),  # Extract the topic from the response
                'imageUrl': self.extract_image_url(response),  # Extract the image URL from the response
                'deadline': ActivityScraper().get_deadline(response.url)  # Extract the deadline from the response URL
            }

        def parse_other(self, response):
            content = ' '.join(response.xpath('//body//text()').extract())  # Extract all text content from the body
            content = normalize(content)  # Normalize the content
            analysis = ActivityScraper().analyze_caption(content)  # Analyze the caption to extract event details
            return {
                'topic': analysis["event_name"],  # Extracted event name
                'imageUrl': self.extract_image_url(response),  # Extract the image URL
                'deadline': analysis["deadline"]  # Extract the deadline
            }

        def extract_topic(self, response):
            main_topic = response.xpath("//meta[@property='og:title']/@content").get()  # Extract topic from meta tag
            if main_topic:
                return main_topic  # Return the extracted topic
            return "General Event"  # Return default topic if none is found

        def extract_image_url(self, response):
            domain = response.url.split('/')[2]  # Extract the domain from the URL
            if 'camphub.in.th' in domain:
                soup = BeautifulSoup(response.text, 'html.parser')  # Parse the HTML content using BeautifulSoup
                competition_image = soup.find('img', class_='wp-post-image')  # Find the main image element
                if competition_image and 'data-src' in competition_image.attrs:
                    return competition_image['data-src']  # Return the image URL
            images = response.xpath("//img/@src").extract()  # Extract all image URLs from the page
            for image_url in images:
                if "data:image" not in image_url:
                    return image_url  # Return the first valid image URL
            return None  # Return None if no valid image URL is found

    def analyze_caption(self, caption: str) -> Dict:
        try:
            language_code = detect(caption)  # Detect the language of the caption
        except Exception as e:
            print(f"An error occurred during language detection: {e}")  # Print error message if detection fails
            language_code = 'unknown'
        language = "unknown"  # Default language
        if language_code == 'en':
            language = 'english'  # Set language to English if detected
        elif language_code == 'th':
            language = 'thai'  # Set language to Thai if detected
        deadline = self.extract_date(caption)  # Extract date from the caption
        event_name_match = re.search(
            r'(?<!\d)(?<!\d )(?:\b[A-Za-z0-9_]+\s?)+(?:Camp|Competition|Event|Festival|Conference|Meetup|Workshop|Talks|Program|Coding|ค่าย|IT)',
            caption,
            re.IGNORECASE
        )  # Regex pattern to match event names
        if not event_name_match:
            event_name_match = re.search(r'(?:\b[A-Za-z0-9_]+\s?)+', caption)  # Fallback pattern to match any text
        event_name = event_name_match.group(0).strip() if event_name_match else None  # Extract the event name
        return {
            "deadline": deadline,  # Return the extracted deadline
            "language": language,  # Return the detected language
            "event_name": event_name  # Return the event name
        }

    def extract_date(self, text):
        thai_months = {  # Mapping of Thai months to their English equivalents
            'มกราคม': 'January', 'กุมภาพันธ์': 'February', 'มีนาคม': 'March', 'เมษายน': 'April',
            'พฤษภาคม': 'May', 'มิถุนายน': 'June', 'กรกฎาคม': 'July', 'สิงหาคม': 'August',
            'กันยายน': 'September', 'ตุลาคม': 'October', 'พฤศจิกายน': 'November', 'ธันวาคม': 'December',
            'ม.ค.': 'Jan', 'ก.พ.': 'Feb', 'มี.ค.': 'Mar', 'เม.ย.': 'Apr',
            'พ.ค.': 'May', 'มิ.ย.': 'Jun', 'ก.ค.': 'Jul', 'ส.ค.': 'Aug',
            'ก.ย.': 'Sep', 'ต.ค.': 'Oct', 'พ.ย.': 'Nov', 'ธ.ค.': 'Dec'
        }

        for thai_month, eng_month in thai_months.items():
            text = text.replace(thai_month, eng_month)  # Replace Thai month names with English equivalents

        date_patterns = [  # Patterns to match different date formats
            r'\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\b',
            r'\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b',
            r'\b(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})\b',
            r'\b(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})\b',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)  # Search for date pattern in the text
            if match:
                try:
                    parsed_date = dateparser.parse(match.group(0), settings={'PREFER_DATES_FROM': 'future'})  # Parse the date
                    if parsed_date and parsed_date.year == datetime.now().year:
                        return parsed_date  # Return the parsed date if it matches the current year
                    elif parsed_date:
                        return parsed_date.replace(year=datetime.now().year)  # Replace year with current year
                except:
                    pass

        try:
            parsed_date = dateparser.parse(text, settings={'PREFER_DATES_FROM': 'future'})  # Parse date from text
            if parsed_date:
                return parsed_date  # Return the parsed date
        except:
            pass

        return None  # Return None if no date is found

    def scrape_post(self, url_or_shortcode: str) -> Dict:
        if "http" in url_or_shortcode:
            shortcode = url_or_shortcode.split("/p/")[-1].split("/")[0]  # Extract shortcode from URL
        else:
            shortcode = url_or_shortcode  # Use the provided shortcode directly
        print(f"Scraping Instagram post: {shortcode}")
        variables = {
            "shortcode": shortcode,
            "child_comment_count": 0,
            "fetch_comment_count": 0,
            "parent_comment_count": 0,
            "has_threaded_comments": False,
        }  # Variables for Instagram GraphQL query
        url = "https://www.instagram.com/graphql/query/?query_hash=b3055c01b4b222b8a47dc12b090e4e64&variables="
        try:
            result = httpx.get(
                url=url + quote(json.dumps(variables)),  # Make a GET request to the Instagram GraphQL endpoint
                headers={"x-ig-app-id": self.INSTAGRAM_APP_ID},
            )
            result.raise_for_status()  # Raise an exception for HTTP errors
            data = result.json()  # Parse the JSON response
        except httpx.RequestError as e:
            print(f"An error occurred while making the request: {e}")  # Print error message for request errors
            return {}
        except httpx.HTTPStatusError as e:
            print(f"An HTTP error occurred: {e.response.status_code} - {e.response.text}")  # Print error message for HTTP errors
            return {}
        except json.JSONDecodeError as e:
            print(f"An error occurred while decoding the JSON response: {e}")  # Print error message for JSON errors
            return {}
        return data.get("data", {}).get("shortcode_media", {})  # Return the media data from the JSON response

    def parse_post(self, data: Dict) -> Dict:
        if not data:
            return {}
        print(f"Parsing post data {data.get('shortcode', 'Unknown shortcode')}")
        result = jmespath.search("""{
            main_image_url: display_url,
            caption: edge_media_to_caption.edges[0].node.text,
            timestamp: taken_at_timestamp,
            is_video: is_video
        }""", data)  # Extract relevant fields from the post data using JMESPath
        return result

    def scrape_event(self, url):
        if 'instagram.com' in url:
            post_data = self.scrape_post(url)  # Scrape post data from Instagram
            parsed_data = self.parse_post(post_data)  # Parse the scraped post data
            if parsed_data:
                analysis = self.analyze_caption(parsed_data.get("caption", ""))  # Analyze the caption for event details
                return {
                    "topic": analysis["event_name"],  # Extracted event name
                    "imageUrl": None if parsed_data.get("is_video", False) else parsed_data.get("main_image_url", "None"),  # Extracted image URL
                    "deadline": analysis["deadline"] or datetime.fromtimestamp(parsed_data.get("timestamp", 0)).isoformat()  # Extracted deadline
                }
            else:
                return None
        else:
            process = CrawlerProcess({
                'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
            })  # Create a Scrapy process with a custom user agent
            event_data = []
            def crawler_results(item, response, spider):
                event_data.append(item)  # Append scraped items to the event_data list
            dispatcher.connect(crawler_results, signal=scrapy.signals.item_scraped)  # Connect the item_scraped signal to the crawler_results function
            process.crawl(self.EventSpider, start_urls=[url])  # Start crawling using the EventSpider
            process.start()  # Block until the crawling is finished
            return event_data[0] if event_data else None  # Return the first scraped item or None

    def run_scrape_event(self, url):
        return self.scrape_event(url)  # Run the scrape_event method with the provided URL