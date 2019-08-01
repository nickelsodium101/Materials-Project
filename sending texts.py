# -*- coding: utf-8 -*-
"""
Created on Wed Jul 31 09:13:07 2019

@author: borodnm1
"""
   
from selenium import webdriver 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 
from selenium.webdriver.common.keys import Keys 
from selenium.webdriver.common.by import By 
import time 
 
# Replace below path with the absolute path 
# to chromedriver in your computer 
#the below line open your chrome browser
 
driver = webdriver.Chrome('/Users/borodnm1/Desktop/chromedriver') 
#the below line will take you to the specific url you have mentioned 
 
driver.get("https://web.whatsapp.com/") 
 
wait = WebDriverWait(driver, 600) 
# Replace 'Friend's Name' with the name of your friend  
# or the name of a group  

#options = webdriver.ChromeOptions()
#options.add_argument("user-data-dir=C:\\Users\\Phoenix\\appdata\\local\Google\\Chrome\\User Data\Default")
#driver = webdriver.Chrome(executable_path=r'C:\Windows\chromedriver.exe', chrome_options=options)

target = '"Group"'
 
# Replace the below string with your own message 
count = 7001
total_count = 10000
filename = '{}.csv'.format('mp-' + str(count) + '_mp-' + str(total_count))

#chrome_options = webdriver.ChromeOptions()
#chrome_options.add_argument('--no-sandbox')
#chrome = webdriver.Chrome('/Users/borodnm1/Desktop/chromedriver', chrome_options=chrome_options)
x_arg = '//span[contains(@title,' + target + ')]'
group_title = wait.until(EC.presence_of_element_located((By.XPATH, x_arg)))
print(group_title)
print("after wait")
group_title.click()
inp = "//div[@contenteditable='true']"
inp_xpath = '//div[@class="input"][@dir="auto"][@data-tab="1"]'
input_box = wait.until(EC.presence_of_element_located((By.XPATH, inp)))
print(input_box)
input_box.send_keys(filename + Keys.ENTER)
input_box.send_keys("Pulling data was successful" + Keys.ENTER)
#this for i in range(100):
#	input_box.send_keys(string + Keys.ENTER)
#	time.sleep(1)





