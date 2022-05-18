Feature: Sales in the store



  Scenario: Add a product to my cart
    Given I'm a customer and I want to buy
    When I add a product to my cart
    Then I should get the products list updated that already are in my cart

  Scenario: Add new product to the catalog store
    Given I'm a manager and I want to setup the store
    When add a product to the catalog
    Then I should get the confirmation message of added product

  Scenario: Decrease a product from stock
    Given I'm a manager store who has products in the catalog
    When It's approved a customer's payment for 2 t-shirt
    Then I should get a decrease in my stock

# Scenario: The customer want to checkout and pay the order from the cart

# Scenario: The customer asks for the checkout status





