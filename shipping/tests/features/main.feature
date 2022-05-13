Feature: Shipping manage orders and returns
  As a web surfer,
  I want to know the state of my order and the products I returned,
  So I can know when my order arrive or if my returns has been accepted.

  # The "@" annotations are tags
  # One feature can have multiple scenarios
  # The lines immediately after the feature title are just comments

  Scenario: Create a new order
    Given a new checkout payed arrived
    When a new order is created
    Then I Should get the order in ordered status
  
  Scenario: Process the created order 
    Given an order created in ordered status
    When the order is completely processed 
    Then I Should get the order in delivered status
  
  



    