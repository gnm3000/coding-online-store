Feature: Customer microservice can manage customers and thier wallets

  Scenario: the customer register to the store
     Given the petition of the customer for registration
      When we receive the full_name and amount USD for the wallet
      Then we save it and return his data

