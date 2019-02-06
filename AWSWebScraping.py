from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import mysql.connector
from config import url, path
from config import host, user, passwd, database, country

try:

    # Start Browser
    browser = webdriver.Firefox()
    url = url
    browser.get(url)

    # Connect to database
    mydb = mysql.connector.connect(
        host=host,
        user=user,
        passwd=passwd,
        database=database
    )
    cursor = mydb.cursor()

    sql = "DROP TABLE IF EXISTS AWSPrice_US"
    cursor.execute(sql)

    # Create Table
    sql = """
        CREATE TABLE AWSPrice_US(
        OS varchar(50),
        Region varchar(50),
        InstanceType varchar(20),
        OfferTerm varchar(50),
        PaymentOption varchar(50),
        UpFront varchar(20),
        Monthly varchar(20),
        EffectiveHourly varchar(20),
        SavingsOverOnDemand varchar(20),
        OnDemandHourly varchar(20)
        ) 
        """
    cursor.execute(sql)
    print("Table Created")

    # Find list of the  OS
    os_list_elem = browser.find_element_by_xpath(path)

    # Move tabs to view
    browser.execute_script("return arguments[0].scrollIntoView(true);", browser.find_element_by_xpath(path))
    browser.execute_script("window.scrollBy(0,-100);")

    # Iterate over the OS list
    for index, os_item in enumerate(BeautifulSoup(os_list_elem.get_attribute('innerHTML'), "html5lib").findAll('li')):

        # OS Elem
        os_elem = browser.find_element_by_xpath(f"/html/body/div[1]/div/div/main/section/div[2]/div[8]/div/ul/li[{index+1!r}]/a")

        # Click on the OS
        browser.execute_script("return arguments[0].click()", os_elem)

        # Find List Of region options
        region_list_elem = browser.find_element_by_xpath(f"/html/body/div[1]/div/div/main/section/div[2]/div[8]/div/div/div[{index+1!r}]/div/div/div/div/div[1]/div/ul")

        # Iterate over region options
        for j, region in enumerate(BeautifulSoup(region_list_elem.get_attribute('innerHTML'), "html5lib").findAll('li')):

            # Click the region list
            browser.execute_script("return arguments[0].click()", region_list_elem)

            # Find region element
            region_elem = browser.find_element_by_xpath(f"/html/body/div[1]/div/div/main/section/div[2]/div[8]/div/div/div[{index+1!r}]/div/div/div/div/div[1]/div/ul/li[{j+1!r}]")

            # Click the region element
            browser.execute_script("return arguments[0].click()", region_elem)

            # Wait for element presence
            WebDriverWait(browser, 30).until(EC.presence_of_element_located, (By.XPATH, f"/html/body/div[1]/div/div/main/section/div[2]/div[8]/div/div/div[{index+1!r}]/div/div/div/div/div[2]/div[{j+1!r}]"))
            # Instances list wrapper element
            instances_list_wrapper_elem = browser.find_element_by_xpath(f"/html/body/div[1]/div/div/main/section/div[2]/div[8]/div/div/div[{index+1!r}]/div/div/div/div/div[2]/div[{j+1!r}]")

            # Instances wrapper element
            instances_wrapper_elem = BeautifulSoup(instances_list_wrapper_elem.get_attribute('innerHTML'), "html5lib").findAll('div', attrs={"class": "aws-pricing-table-wrapper"})

            # Iterate over the Instances
            for k, instance_type_div in enumerate(instances_wrapper_elem):
                # Instance Type Name in h2
                instance_type = instance_type_div.h2.contents[0].strip()
                # Iterate over tables
                for l, offer_term_table in enumerate(instance_type_div.findAll('table')):
                    # Offer Term
                    offer_term = offer_term_table.find('th', attrs={'class': 'aws-term'}).contents[0].strip()
                    # On demand is only ove value for all the rows
                    onDemandHourly = offer_term_table.find('td', attrs={'class': 'aws-onDemandHourly'}).contents[0].strip()

                    # Iterate over Table Rows
                    for m, purchase_option_row in enumerate(offer_term_table.findAll('tr', attrs={'class': 'aws-purchase-options'})):
                        purchase_option = purchase_option_row.find('td', attrs={'class': 'aws-purchaseOption'}).contents[0].strip()
                        upfront = purchase_option_row.find('td', attrs={'class': 'aws-upfront'}).contents[0].strip()
                        monthly = purchase_option_row.find('td', attrs={'class': 'aws-monthlyStar'}).contents[0].strip()
                        hourly = purchase_option_row.find('td', attrs={'class': 'aws-effectiveHourly'}).abbr.contents[0].strip()
                        savingsOverOD = purchase_option_row.find('td', attrs={'class': 'aws-savingsOverOD'}).contents[0].strip()
                        # print(os_item.text,region.text,instance_type,offer_term,purchase_option,upfront,monthly,hourly,savingsOverOD,onDemandHourly)

                        if country in region.text:
                            # Insert Data
                            sql = """
                            INSERT INTO AWSPrice_US
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            """
                            cursor.execute(sql, [os_item.text, region.text, instance_type, offer_term, purchase_option, upfront, monthly, hourly, savingsOverOD, onDemandHourly])
                            # Save data to database
                            mydb.commit()
finally:
    browser.close()
    mydb.close()
