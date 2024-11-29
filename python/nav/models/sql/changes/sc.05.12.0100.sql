-- Increase alertprofiles dropdown list limits
UPDATE matchfield
SET list_limit = 10000
WHERE show_list
  AND list_limit = 1000;
