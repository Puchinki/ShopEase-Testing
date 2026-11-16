# ShopEase – US-001 Functional Testing Guide

## Story under test

**Story ID:** US-001  
**Title:** Register a new customer account  
**User story:** As a first-time visitor, I want to create an account so that I can save my details and manage my orders.

## Preconditions

1. The ShopEase demo is open at `http://localhost:8000`.
2. Use Chrome or another modern desktop browser.
3. Use fictional test data only.
4. For a clean test, select **Reset all local demo accounts** and confirm.

## Test data

| Purpose | Test data |
|---|---|
| Valid name | Asha / Sharma |
| Valid DOB | 1995-04-15 |
| Valid email | asha.demo@example.com |
| Valid mobile | 9876543210 |
| Valid password | Test@1234 |
| Confirm password | Test@1234 |
| Valid demo OTP | 123456 |
| Invalid OTP | 000000 |
| Invalid email | asha.demo@ or asha.example.com |
| Invalid mobile | 987654321 or 98AB543210 |
| Weak password | test1234 or TEST@1234 |

Use a new email and mobile for each successful registration. To test duplicate detection, first register the sample account successfully and then try it again.

## Suggested functional test cases

| Test Case ID | Scenario | Steps / Test Data | Expected Result |
|---|---|---|---|
| TC-US001-001 | Register with valid details | Enter all valid sample values, accept terms, Continue, enter OTP 123456 | One active account is created and success confirmation is displayed. |
| TC-US001-002 | Submit all fields blank | Select Continue without entering values | Submission is blocked and required-field messages are displayed. |
| TC-US001-003 | First name is mandatory | Leave First name blank; complete other fields correctly | First name required message is displayed; OTP step does not open. |
| TC-US001-004 | Last name is mandatory | Leave Last name blank; complete other fields correctly | Last name required message is displayed; OTP step does not open. |
| TC-US001-005 | Name minimum length | Enter a one-character first or last name | A 2–50 character validation message is displayed. |
| TC-US001-006 | Name maximum length | Enter a 51-character first or last name | A 2–50 character validation message is displayed. |
| TC-US001-007 | Name allowed characters | Enter a name containing digits or unsupported punctuation | The allowed-character validation message is displayed. |
| TC-US001-008 | Name allowed punctuation | Enter names such as Anne-Marie and O'Neil | Names are accepted when all other values are valid. |
| TC-US001-009 | DOB is mandatory | Leave DOB blank | Date of birth required message is displayed. |
| TC-US001-010 | Underage customer | Enter a DOB that makes the customer 17 years old today | Registration is blocked with the minimum-age message. |
| TC-US001-011 | Exactly 18 years old | Enter the date that makes the customer turn 18 today | DOB passes the age rule. |
| TC-US001-012 | Invalid email format | Enter `asha.demo@` | Valid-email message is displayed. |
| TC-US001-013 | Email missing @ | Enter `asha.example.com` | Valid-email message is displayed. |
| TC-US001-014 | Email maximum length | Enter an email address longer than 100 characters | Maximum-length message is displayed. |
| TC-US001-015 | Duplicate email | Register `asha.demo@example.com`, then attempt another account with the same email | Duplicate email message is displayed; no second account is created. |
| TC-US001-016 | Duplicate email with different case | After registering lowercase email, enter `ASHA.DEMO@example.com` | Duplicate detection works without case sensitivity. |
| TC-US001-017 | Mobile has 9 digits | Enter `987654321` | Exactly-10-digits validation message is displayed. |
| TC-US001-018 | Mobile has letters | Enter `98AB543210` | Exactly-10-digits validation message is displayed. |
| TC-US001-019 | Mobile has 11 digits | Enter `98765432101` | Exactly-10-digits validation message is displayed. |
| TC-US001-020 | Duplicate mobile | Register a mobile number, then attempt a second account using the same mobile and a different email | Duplicate mobile message is displayed; no second account is created. |
| TC-US001-021 | Password below 8 characters | Enter a 7-character password | Password policy message is displayed. |
| TC-US001-022 | Password missing uppercase | Enter `test@1234` | Password policy message is displayed. |
| TC-US001-023 | Password missing lowercase | Enter `TEST@1234` | Password policy message is displayed. |
| TC-US001-024 | Password missing digit | Enter `Test@abcd` | Password policy message is displayed. |
| TC-US001-025 | Password missing special character | Enter `Test1234` | Password policy message is displayed. |
| TC-US001-026 | Confirm password mismatch | Password `Test@1234`, confirm `Test@12345` | Confirm-password mismatch message is displayed. |
| TC-US001-027 | Terms not accepted | Complete all fields correctly but leave checkbox unchecked | Registration is blocked and terms acceptance message is shown. |
| TC-US001-028 | Incorrect OTP | Complete valid registration details, continue, enter `000000` | Account is not created; incorrect OTP message is displayed. |
| TC-US001-029 | OTP has fewer than 6 digits | Enter `12345` | Six-digit OTP validation message is displayed. |
| TC-US001-030 | OTP expires | Continue to OTP and wait until the 5-minute countdown ends, then enter `123456` | Expired OTP message is displayed; account is not created. |
| TC-US001-031 | Correct OTP after invalid OTP | Enter `000000`, then correct it to `123456` before expiry | Account is created once after valid OTP. |
| TC-US001-032 | Back from OTP | Continue to OTP, select Back to details, correct a field and continue again | User returns to the form; updated information is used for the new verification attempt. |
| TC-US001-033 | Password is masked | Type a password without selecting Show | Password characters are masked. |
| TC-US001-034 | Password visibility toggle | Select Show and then Hide | Password is readable when Show is selected and masked again when Hide is selected. |
| TC-US001-035 | Terms page opens | Select Terms and Conditions | Sample terms dialog opens and can be closed. |
| TC-US001-036 | Account persists after refresh | Successfully register an account, refresh browser, then attempt same email/mobile again | Account remains saved in that browser and duplicate checks still work. |

## Test execution record

Copy this table into Excel or a test management tool and complete it during execution.

| Test Case ID | Actual Result | Status (Pass/Fail/Blocked/Not Run) | Defect ID | Executed By | Execution Date |
|---|---|---|---|---|---|
| TC-US001-001 |  | Not Run |  |  |  |
| TC-US001-002 |  | Not Run |  |  |  |
| TC-US001-003 |  | Not Run |  |  |  |

## Important testing notes

- Do not mark a test as Pass just because the page looks correct. Check the actual behaviour and account creation result.
- After a successful registration, reuse the same email and mobile only when testing duplicate detection.
- The browser stores demo accounts locally. Different browser profiles have separate data.
- The 5-minute OTP expiry is an implementation assumption for this practice build because the original business requirement did not specify an expiry duration.
- If the actual result differs from the documented expected result, capture the steps, test data, screenshot, expected result and actual result in a defect report.
