from pytest_bdd import scenarios

scenarios(
    'features/admin/alert_details.feature',
)
# from selenium.webdriver.support.wait import WebDriverWait
#
#
# @scenario('bdd/admin_test_alerts.feature', 'Adding alerts')
# def test_alerts(live_server, selenium):
#     pass
#
#
# @given("I'm logged as an admin user")
# def login(live_server, admin, selenium):
#     selenium.get(live_server.url)
#     selenium.find_element_by_id("id_username").send_keys(admin.email)
#     selenium.find_element_by_id("id_password").send_keys('12345.Abcde')
#     selenium.find_element_by_css_selector("input[type='submit']").click()
#     WebDriverWait(selenium, 2).until(lambda s: s.find_element_by_xpath('//*[@id="site-name"]/a[2]'))
#     assert selenium.find_element_by_xpath('//*[@id="site-name"]/a[2]').text == "Otwarte Dane"
#
#
# @when("I go to the alerts page")
# def go_to_listing(selenium):
#     selenium.find_element_by_xpath('//*[@id="left-nav"]/ul/li[5]/a').click()
#     WebDriverWait(selenium, 2).until(lambda s: s.find_element_by_xpath('//*[@id="changelist"]/div/div[1]/a'))
#     assert selenium.find_element_by_xpath('//*[@id="suit-center"]/ul/li[3]').text == 'Komunikaty'
#
#
# @then("the alerts page is empty")
# def check_if_no_alerts(selenium):
#     assert selenium.find_element_by_xpath(
#         '//*[@id="changelist-form"]/div').text == 'Komunikaty nie są jeszcze utworzone. Dodaj Komunikat'
#
#
# @then("I click ADD button")
# def click_add_btn(selenium):
#     btn = selenium.find_element_by_xpath('//*[@id="changelist"]/div/div[1]/a')
#     assert btn.text.strip() == 'Dodaj Komunikat'
#     btn.click()
#     WebDriverWait(selenium, 2).until(lambda s: s.find_element_by_xpath('//*[@id="suit-center"]/ul/li[4]'))
#     assert selenium.find_element_by_xpath('//*[@id="suit-center"]/ul/li[4]').text.strip() == 'Dodaj Komunikat'
#
#
# @then("I fill the form")
# def fill_the_form(selenium):
#     pass
#
#
# @then("I click SAVE button")
# def save_form(selenium):
#     pass
