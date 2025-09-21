from playwright.sync_api import sync_playwright, expect

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # Go to the admin page
    page.goto("http://127.0.0.1:5000/admin.html")

    # Click on the first alert
    alert_item = page.locator("#alertList li").first
    alert_item.click()

    # Verify that the modal is visible
    modal = page.locator("#alertModal")
    expect(modal).to_be_visible()

    # Verify the content of the modal
    expect(modal).to_contain_text("Blockchain ID: abcdef123456")
    expect(modal).to_contain_text("Phone Number: 111-222-3333")
    expect(modal).to_contain_text("KYC: kyc123")
    expect(modal).to_contain_text("Emergency Contact: 444-555-6666")
    expect(modal).to_contain_text("Location: 34.0522, -118.2437")

    # Take a screenshot
    page.screenshot(path="jules-scratch/verification/verification.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
