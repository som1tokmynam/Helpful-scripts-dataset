import requests
from bs4 import BeautifulSoup
import os
import re
import time

def sanitize_filename(name):
    """Removes characters from a string that are not allowed in filenames."""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.replace(' ', '_')
    return name

def scrape_character_page_content(character_url):
    """Scrapes the text content from a single character's Fandom page."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        response = requests.get(character_url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"  -> Error fetching page {character_url}: {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    content_div = soup.find('div', class_='mw-parser-output')
    
    if not content_div:
        print(f"  -> Could not find main content for {character_url}")
        return ""

    paragraphs = content_div.find_all('p', recursive=True)
    full_text = "\n\n".join([p.get_text().strip() for p in paragraphs])
    return full_text

def scrape_and_save_all_characters(start_url, output_dir="characters"):
    """
    Scrapes all characters from a Fandom category, handling pagination,
    and saves each one into a separate text file.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    current_page_url = start_url
    total_characters_found = 0
    page_num = 1

    # Loop through all pages of the character category
    while current_page_url:
        print(f"\n--- Scraping Page {page_num} ---")
        print(f"URL: {current_page_url}")
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
            response = requests.get(current_page_url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Fatal Error: Could not fetch category page: {e}")
            break # Exit the loop if a page fails to load

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Scrape characters from the current page
        character_list_container = soup.find('div', class_='category-page__members')
        if not character_list_container:
            print("Could not find character container on this page. Stopping.")
            break
            
        character_links = character_list_container.find_all('a', class_='category-page__member-link')
        
        if not character_links:
            print("No more character links found. Process might be complete.")
            break
            
        total_characters_found += len(character_links)
        print(f"Found {len(character_links)} characters on this page. Total found so far: {total_characters_found}")

        # Process each character link on the current page
        for link in character_links:
            character_name = link.get_text().strip()
            character_page_url = link.get('href')
            
            if not character_page_url.startswith('http'):
                base_url = "https://wingsoffire.fandom.com"
                character_page_url = base_url + character_page_url

            print(f"Processing: {character_name}")
            content = scrape_character_page_content(character_page_url)
            
            if content:
                filename = sanitize_filename(character_name) + ".txt"
                filepath = os.path.join(output_dir, filename)
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"  -> Saved to {filepath}")
                except IOError as e:
                    print(f"  -> Error saving file for {character_name}: {e}")
            else:
                print(f"  -> No content retrieved for {character_name}")

            # Small delay to be polite to the server and avoid getting blocked
            time.sleep(0.5) 

        # --- PAGINATION LOGIC ---
        # Find the "Next" link to go to the next page
        pagination_container = soup.find('div', class_='category-page__pagination')
        if pagination_container:
            next_link = pagination_container.find('a', class_='category-page__pagination-next')
            if next_link and next_link.has_attr('href'):
                current_page_url = next_link['href']
                page_num += 1
            else:
                # No "Next" link found, so we are on the last page
                current_page_url = None
        else:
            # No pagination container found, must be only one page
            current_page_url = None

    print(f"\nScraping process complete! Found a total of {total_characters_found} characters.")


if __name__ == "__main__":
    WINGS_OF_FIRE_CHARACTERS_URL = "https://wingsoffire.fandom.com/wiki/Category:Characters"
    OUTPUT_DIRECTORY = "Wings_of_Fire_Characters"
    
    scrape_and_save_all_characters(WINGS_OF_FIRE_CHARACTERS_URL, output_dir=OUTPUT_DIRECTORY)