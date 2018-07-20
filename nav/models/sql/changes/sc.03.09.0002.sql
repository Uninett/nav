-- get macwatch into event system's subsystem list
INSERT INTO subsystem (
  SELECT 'macwatch' AS name 
  WHERE NOT EXISTS (
    SELECT name FROM subsystem WHERE name='macwatch'));
