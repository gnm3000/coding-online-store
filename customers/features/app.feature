Feature: Customer microservice can manage customers and thier wallets
  
  Scenario: the customer register to the store
    Given the petition of the customer for registration
    When we receive the full_name and amount USD for the wallet
    Then I should get a confirmation insertion message


  Scenario: the customer bought something and the business updated his wallet account
    Given An order is being processed by an amount in usd
    When we update the customer wallet
    Then I should get his new balance




    