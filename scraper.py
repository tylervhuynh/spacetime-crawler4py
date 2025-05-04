import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup


def scraper(url, resp, unique_pages, subdomains, text_cache, token_cache):
    valid_links = []
    links = extract_next_links(url, resp)
    for link in links:
        # Avoids crawler traps by ensuring links are unique
        num_pages = len(unique_pages)  # Gets number of unique pages found so far
        unique_pages.add(link)      # Adds unique page to a set
        if num_pages + 1 != len(unique_pages): # If page is not unique, skip it
            continue

        if is_valid(link):
            parsed = urlparse(link) # Parses link

            # Tracks subdomains and their number of pages
            if parsed.netloc in subdomains:
                subdomains[parsed.netloc] += 1
            else:
                subdomains[parsed.netloc] = 1

            # Filtering for low/high information (<10 words or >1000000)
            soup = BeautifulSoup(resp.raw_response.content, 'lxml')
            for tag in soup.find_all(['script', 'style', 'noscript', 'header', 'footer']):
                tag.decompose()
            text = soup.get_text(separator=' ', strip=True)
            words = text.lower().split()
            word_count = len(words)
            if word_count < 10 or word_count > 100000:
                continue

            valid_links.append(link)

            # Filters exact duplicates
            if text not in text_cache:
                text_cache.add(text)
                if len(text_cache) > 100: # Limit cache size
                    text_cache.pop()
            else:
                continue

            # Filters near duplicates
            frequencies = compute_word_frequencies(words)
            if is_near_duplicate(frequencies, token_cache):
                continue  # Too similar to a recent page
            token_cache.append(frequencies)
            if len(token_cache) > 100: # Limit cache size
                token_cache.pop(0)

            # Logging information
            with open("urlcontents.txt", 'a', encoding='UTF-8') as file:
                file.write("URL #" + str((len(unique_pages) + 1)) + ": " + link)
                file.write('\n' + text + '\n')
                file.write("\nTYLERHUYNHSEPERATOR\n")

    with open("pages.txt", 'w', encoding='UTF-8') as file:
        file.write("Number of Unique Pages Found: " + str(len(unique_pages)) + '\n\n')
        file.write("Number of Unique Pages Found for Each Subdomain:\n")
        for subdomain in subdomains:
            file.write(subdomain + " " + str(subdomains[subdomain]) + "\n")
        file.write("\nThe unique pages found were:\n")
        counter = 1
        for page_link in unique_pages:
            file.write("URL #" + str(counter) + ": " + page_link + "\n")
            counter += 1
    return valid_links # ORIGINAL: [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    if resp.status != 200:
        print("Error occurred while extracting links from url:", resp.error)
        return list()
    extracted_links = []
    try:
        soup = BeautifulSoup(resp.raw_response.content, 'lxml')
        links = soup.find_all('a')
        for link in links:
            href = link.get('href')
            if href:
                full_url = urljoin(resp.url, href)
                full_url, _ = urldefrag(full_url)
                extracted_links.append(full_url)
    except Exception as e:
        print("Error occurred while extracting a specific link:", e)
    return extracted_links

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        # Only allows valid domains
        valid_domains = {"ics.uci.edu", "cs.uci.edu", "informatics.uci.edu",
                         "stat.uci.edu", "today.uci.edu"}
        if "today.uci.edu" in parsed.netloc and not parsed.path.startswith("/department/information_computer_sciences/"):
            return False
        if not any(domain in parsed.netloc for domain in valid_domains):
            return False

        # Avoids calendar, and date traps
        if ("calendar" in parsed.path or "/month" in parsed.path or 
            "/day" in parsed.path or "/events" in parsed.path):
                return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf|jpg|jpeg"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise

def is_near_duplicate(frequencies, token_cache):
    for cached_dictionary in token_cache:
        intersections = number_of_intersections(frequencies, cached_dictionary)
        min_length = min(len(frequencies), len(cached_dictionary))
        if min_length == 0:
            continue  # Avoids division by zero
        similarity = intersections / min_length
        if similarity >= 0.9:
            return True
    return False

# From Assignment 1: Text Processing
def compute_word_frequencies(tokens: list) -> dict:
    frequencies = {}
    for token in tokens:
        if token not in frequencies:
            frequencies[token] = 1 # Adds token to frequencies dictionary
        else:
            frequencies[token] += 1 # Increments token's frequency in dictionary
    return frequencies

def number_of_intersections(frequencies1: dict, frequencies2: dict):
    # First picks smaller dictionary to traverse with, all O(1) instructions
    if len(frequencies1) <= len(frequencies2):
        smaller_frequencies = frequencies1
        larger_frequencies = frequencies2
    else:
        smaller_frequencies = frequencies2
        larger_frequencies = frequencies1

    # Traverses one dictionary, seeking intersections, O(N)
    counter = 0
    for token in smaller_frequencies.keys():
        if token in larger_frequencies:
            counter += 1
    return counter
