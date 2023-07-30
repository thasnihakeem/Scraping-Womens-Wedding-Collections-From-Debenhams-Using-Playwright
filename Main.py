import re
import random
import asyncio
import pandas as pd
from playwright.async_api import async_playwright

async def perform_request_with_retry(page, url):
    MAX_RETRIES = 10
    retry_count = 0

    while retry_count < MAX_RETRIES:
        try:
            await page.goto(url, timeout=600000)  # Increase the timeout to 90 seconds
            break
        except:
            retry_count += 1
            if retry_count == MAX_RETRIES:
                raise Exception("Request timed out")
            await asyncio.sleep(random.uniform(1, 5))

async def get_product_urls(page):
    product_urls = set()

    while True:
        all_items = await page.query_selector_all('.link__Anchor-xayjz4-0.daQcrV')
        if not all_items:
            break

        for item in all_items:
            url = await item.get_attribute('href')
            full_url = 'https://www.debenhams.com' + url
            product_urls.add(full_url)

        num_products = len(product_urls)
        print(f"Scraped {num_products} products.")

        load_more_button = await page.query_selector(
            '.link__Anchor-xayjz4-0.hlgxPa[data-test-id="pagination-load-more"]')
        if load_more_button:
            next_page_url = await load_more_button.get_attribute('href')
            next_page_url = 'https://www.debenhams.com' + next_page_url
            await perform_request_with_retry(page, next_page_url)
        else:
            break

    return list(product_urls)

async def get_product_name(page):
    try:
        product_name_elem = await page.query_selector('.heading__StyledHeading-as990v-0.XbnMa')
        product_name = await product_name_elem.text_content()
    except:
        product_name = "Not Available"
    return product_name

async def get_brand_name(page):
    try:
        brand_name_elem = await page.query_selector('.text__StyledText-sc-14p9z0h-0.fRaSnP')
        brand_name = await brand_name_elem.text_content()
    except:
        brand_name = "Not Available"
    return brand_name

async def get_sku(page):
    try:
        sku_element = await page.query_selector('span[data-test-id="product-sku"]')
        sku = await sku_element.inner_text()
    except:
        sku = "Not Available"
    return sku

async def get_image_url(page):
    try:
        image_element = await page.query_selector('img[class="image__Img-sc-1114ukl-0 jWYJzM"]')
        image_url = await image_element.get_attribute('src')
    except:
        image_url = "Not Available"
    return image_url

async def scroll_page(page, scroll_distance):
    await page.evaluate(f"window.scrollBy(0, {scroll_distance});")

async def get_star_rating(page):
    try:
        await scroll_page(page, 1000)
        await page.wait_for_timeout(2000)
        star_rating_elem = await page.wait_for_selector(".heading__StyledHeading-as990v-0.ggFWmZ.starsTotal")
        star_rating_text = await star_rating_elem.inner_text()
    except:
        star_rating_text = "Not Available"
    return star_rating_text

async def get_num_reviews(page):
    try:
        num_reviews_elem = await page.wait_for_selector('.button__Btn-d2s7uk-0.gphIMb .button__Container-d2s7uk-1.gnalpa')
        num_reviews_text = await num_reviews_elem.inner_text()
        num_reviews = re.findall(r'\d+', num_reviews_text)[0]
    except:
        num_reviews = "Not Available"
    return num_reviews

async def get_MRP(page):
    try:
        MRP_elem = await page.query_selector(".text__StyledText-sc-14p9z0h-0.gKDxvK")
        MRP = await MRP_elem.text_content()
        MRP = MRP.replace('£', '')
    except:
        try:
            MRP_elem = await page.query_selector('.text__StyledText-sc-14p9z0h-0.gtCFP')
            MRP = await MRP_elem.text_content()
            MRP = MRP.replace('£', '')
        except:
            MRP = "Not Available"
    return MRP

async def get_sale_price(page):
    try:
        sale_price_element = await page.query_selector('.text__StyledText-sc-14p9z0h-0.gtCFP')
        sale_price = await sale_price_element.text_content()
        sale_price = sale_price.replace('£', '')
    except:
        sale_price = "Not Available"
    return sale_price

async def get_discount_percentage(page):
    try:
        discount_element = await page.query_selector('span[data-test-id="product-price-saving"]')
        discount_text = await discount_element.text_content()
        discount_percentage = re.search(r'\d+', discount_text).group()
    except:
        discount_percentage = "Not Available"
    return discount_percentage

async def get_colour(page):
    try:
        color_element = await page.query_selector('.text__StyledText-sc-14p9z0h-0.gYrIYG')
        color = await color_element.inner_text()
    except:
        color = "Not Available"
    return color

async def get_description(page):
    try:
        description_element = await page.wait_for_selector('div[data-theme-tabs--content="true"]')
        description = await description_element.inner_text()
    except:
        description = "Not Available"
    return description

async def get_details_and_care(page):
    try:
        element = await page.query_selector('.html__HTML-sc-1fx37p7-0.kxhQqn')
        text = await element.inner_text()
    except:
        text = "Not Available"
    return text

async def main():
    async with async_playwright() as pw:
        browser = await pw.firefox.launch()
        page = await browser.new_page()
        await perform_request_with_retry(page, 'https://www.debenhams.com/category/womens-wedding')
        product_urls = await get_product_urls(page)
        df_1 = pd.DataFrame({'Product URL': product_urls})
        df_1.to_csv('product_urls.csv', index=False)
        print("Product URLs saved to product_urls.csv")

        data = []
        for i, url in enumerate(product_urls):
            await perform_request_with_retry(page, url)

            product_name = await get_product_name(page)
            brand = await get_brand_name(page)
            sku = await get_sku(page)
            image_url = await get_image_url(page)
            star_rating = await get_star_rating(page)
            num_reviews = await get_num_reviews(page)
            MRP = await get_MRP(page)
            sale_price = await get_sale_price(page)
            discount_percentage = await get_discount_percentage(page)
            colour = await get_colour(page)
            description = await get_description(page)
            details_and_care = await get_details_and_care(page)

            if i % 10 == 0 and i > 0:
                print(f"Processed {i} links.")

            if i == len(product_urls) - 1:
                print(f"All information for url {i} has been scraped.")

            data.append((url, product_name, brand, sku, image_url, star_rating, num_reviews, MRP,
                         sale_price, discount_percentage, colour, description, details_and_care))

        df = pd.DataFrame(data, columns=['product_url', 'product_name', 'brand', 'sku', 'image_url', 'star_rating', 'number_of_reviews',
                                   'MRP', 'sale_price', 'discount_percentage', 'colour', 'description', 'details_and_care'])
        df.to_csv('product_data.csv', index=False)
        print('CSV file has been written successfully.')

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())

