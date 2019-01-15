-- increase the artificial list limits of alert profile filter match fields
UPDATE matchfield SET list_limit=1000 WHERE list_limit < 1000;
