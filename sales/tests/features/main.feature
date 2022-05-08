Feature: Sales in the store
  As a web surfer,
  I want to buy fashion products,
  So I can add products to my shopping cart and checkout.

  # The "@" annotations are tags
  # One feature can have multiple scenarios
  # The lines immediately after the feature title are just comments

  Scenario: Add a product to my cart
    Given the a product to add to my cart
    When add a product to the cart
    Then get the products list updated that already are in my cart 

  Scenario: Add new product to the catalog store
    Given the a product to add to the catalog store
    When add a product to the catalog
    Then get the confirmation message of added product 
  
  Scenario: The customer want to checkout and pay the order from the cart
    Given -
    When -
    Then -
  Scenario: The customer asks for the checkout status 
    Given -
    When -
    Then -
  
  



    