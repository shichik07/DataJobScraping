# -*- coding: utf-8 -*-
"""
Created on Wed Oct 30 10:47:52 2024

@author: juliu
"""
import warnings
warnings.filterwarnings("ignore")
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from datetime import datetime
import pandas as pd
import time
import math

# web scraper class
class AB_Scraper():
    def __init__(self, URL):
        self.searches = ["Data Analyst", "Datenanalyse", "Data Science"]
        self.url = URL
        self.date = datetime.today().strftime('%d-%m-%d')
        self.source ="BA website"
        self.search_term = "Statistik"
        # create an empyt dataframe
        self.job_ads = pd.DataFrame({
            'Title': pd.Series(dtype='str'),
            'Company': pd.Series(dtype='str'),
            'JobType': pd.Series(dtype='str'),
            'Published': pd.Series(dtype='datetime64[ns]'),
            'Scrp_date': pd.Series(dtype='datetime64[ns]'),
            'Source': pd.Series(dtype='str'),
            'Search_Term':pd.Series(dtype='str'),
            'Link': pd.Series(dtype='str')
        })
        
    def init_webdriver(self):
        """
        Call the BA Website
        """
        try:
            self.driver = webdriver.Chrome()
        except:
            self.driver = webdriver.Chrome()(ChromeDriverManager(version="114.0.5735.90").install())
        # Access the BA page
        self.driver.get(self.url) 
        # Add a small delay to ensure shadow DOM is fully loaded
        time.sleep(0.5)
        
    def check_cookies(self):
        """
        Check the cookie settings
        """
        time.sleep(3)
        shadow_host = self.driver.find_element(By.TAG_NAME, "bahf-cookie-disclaimer-dpl3")
        # Open the element
        shadow_root = self.driver.execute_script('return arguments[0].shadowRoot', shadow_host)
        # Find the cookie button and select it
        cookie_button = shadow_root.find_element(By.CSS_SELECTOR, "button.ba-btn.ba-btn-contrast")
        cookie_button.click()
        time.sleep(1)
    
    def new_row(self, itm):
        """
        generates a new row
        """
        new_row = {
            'Title': self.driver.find_element(by='id', value='eintrag-'+ str(itm) +'-titel').text,
            'Company': self.driver.find_element(by='id', value='eintrag-'+ str(itm) +'-arbeitgeber').text,
            'JobType': self.driver.find_element(by='id', value='eintrag-'+ str(itm) +'-hauptberuf').text,
            'Published': self.driver.find_element(by='id', value='eintrag-'+ str(itm) +'-datum').get_attribute("title").split()[1],
            'Scrp_date': self.date,
            'Source': self.source,
            'Search_Term':self.search_term,
            'Link': self.driver.find_element(By.ID, "ergebnisliste-item-"+ str(itm)).get_attribute("href")
        }
        return new_row
        
    def scrape_data(self):
        """
        Scrape the data on the site
        """
        # find the number of jobs in the list
        nr_entry = int(self.driver.find_element(by='id', value="suchergebnis-h1-anzeige").text.split()[0])
        if nr_entry <= 25:
            for itm in range(nr_entry):
                #create a new row
                n_row = self.new_row(itm)
                # save row
                self.job_ads = pd.concat([self.job_ads, pd.DataFrame([n_row])], ignore_index=True)
        else:
            # find the number of iterations we need to go through (we have 25 )
            nr_rounds = math.ceil(nr_entry/25)
            #default index
            ind = 0
            for rd in range(nr_rounds):
                if nr_rounds - (rd+1) >= 1:
                    for itm in range(ind, ind+25):
                       #create a new row
                       n_row = self.new_row(itm)
                       # save row
                       self.job_ads = pd.concat([self.job_ads, pd.DataFrame([n_row])], ignore_index=True)
                       ind+=1
                    # load more results once the loop is through
                    load_more = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "ergebnisliste-ladeweitere-button"))
                    )
                    self.driver.execute_script("arguments[0].click();", load_more)
                    time.sleep(1)
                else:
                    for itm in range(ind, nr_entry):
                       #create a new row
                       n_row = self.new_row(itm)
                       # save row
                       self.job_ads = pd.concat([self.job_ads, pd.DataFrame([n_row])], ignore_index=True)
                       ind+=1 
                       
    def update_query(self):
        """
        Use different search terms
        """
        for term in self.searches:
            # update term
            self.search_term = term
            # send new search term
            search_box = self.driver.find_element(By.ID, "was-input")
            search_box.clear()  # clears any existing text
            search_box.send_keys(term)
            search_box.send_keys(Keys.RETURN) # press send
            # wait a hard second
            time.sleep(1)
            # scrape data
            self.scrape_data()
                
    def run(self):
        """
        Execute all individual steps
        """
        # initialize the driver
        self.init_webdriver()
        # take care of the cookies
        self.check_cookies()
        # run the first term
        self.scrape_data()
        # run the other terms
        self.update_query()
        #quit driver
        self.driver.quit()
        # return the data to be saved
        return self.job_ads
        
        


url = 'https://www.arbeitsagentur.de/jobsuche/suche?angebotsart=1&pav=true&umkreis=25&was=Statistik&wo=Berlin'

# initiate scraper
ba_scrap = AB_Scraper(URL=url)
# get data
data = ba_scrap.run()
#save the data
data.to_csv(path_or_buf="D:/Data/Dropbox/LifeAfter/PracticeProjects/JobData/out.csv")

