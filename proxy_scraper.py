# proxy_scraper.py

import requests
from bs4 import BeautifulSoup
import random
import logging
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ProxyScraper:
    """
    A class to scrape and verify proxies from https://www.sslproxies.org/.
    
    Attributes:
        user_agents (list): A list of user-agent strings to rotate through for each request.
        session (requests.Session): A session object with a custom retry strategy.
        proxies (list): A list of proxy strings fetched from the website.
    """
    
    def __init__(self, user_agents=None):
        """
        Initializes the ProxyScraper object.
        
        Args:
            user_agents (list, optional): A list of user-agent strings. If not provided, a default list is used.
        """
        if user_agents:
            self.user_agents = user_agents
        else:
            self.user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 OPR/77.0.4054.277",
            ]
        self.session = self.create_session()
        self.proxies = []

    def create_session(self):
        """
        Creates a requests session with a custom retry strategy.
        
        Returns:
            requests.Session: A session object with a custom retry strategy.
        """
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def fetch_proxies(self):
        """
        Fetches a list of proxies from https://www.sslproxies.org/.
        
        Returns:
            list: A list of proxy strings in the format 'ip:port'.
        """
        url = "https://www.sslproxies.org/"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            proxy_table = soup.find("table", {"id": "proxylisttable"})
            proxies = []
            for row in proxy_table.find_all("tr")[1:]:
                data = row.find_all("td")
                proxy = f"{data[0].text}:{data[1].text}"
                proxies.append(proxy)
            return proxies
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching proxies: {e}")
            return []

    def verify_proxy(self, proxy):
        """
        Verifies if a proxy is working by sending a request to https://www.google.com.
        
        Args:
            proxy (str): A proxy string in the format 'ip:port'.
        
        Returns:
            bool: True if the proxy is working, False otherwise.
        """
        test_url = "https://www.google.com"
        headers = {'User-Agent': random.choice(self.user_agents)}
        proxy_dict = {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}"
        }
        try:
            response = self.session.get(test_url, headers=headers, proxies=proxy_dict, timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logging.error(f"Error verifying proxy {proxy}: {e}")
            return False

    def run(self):
        """
        Runs the proxy scraping and verification process.
        
        This method fetches a list of proxies, verifies each proxy, and saves the working proxies to a file 'proxy.txt'.
        """
        try:
            self.proxies = self.fetch_proxies()
            if not self.proxies:
                logging.warning("No proxies found on the website.")
                return

            random.shuffle(self.proxies)
            verified_proxies = [proxy for proxy in self.proxies if self.verify_proxy(proxy)]
            with open("proxy.txt", "w") as file:
                file.write("\n".join(verified_proxies))
            logging.info(f"Working proxies saved to proxy.txt ({len(verified_proxies)} proxies)")
        except Exception as e:
            logging.error(f"Error running ProxyScraper: {e}")

if __name__ == "__main__":
    scraper = ProxyScraper()
    scraper.run()