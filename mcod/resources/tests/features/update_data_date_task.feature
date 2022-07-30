  @periodic_task
  Scenario: Auto update data date task revalidates remote file resource
    Given remote file resource with enabled auto data date update and id 1099
    When update data date task for resource with id 1099 is executed
    Then resource with id 1099 has 2 file validation results

  @periodic_task
  Scenario: Auto update data date task doesnt revalidates api resource
    Given resource with id 1100 and status published and data date update periodic task with interval schedule
    When update data date task for resource with id 1100 is executed
    Then resource with id 1100 has 1 link validation results
