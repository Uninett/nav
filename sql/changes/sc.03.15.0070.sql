-- Create basic token storage for api tokens

CREATE TABLE manage.apitoken (
  id SERIAL PRIMARY KEY,
  token VARCHAR not null,
  expires TIMESTAMP not null,
  client INT REFERENCES profiles.account(id),
  scope INT DEFAULT 0
);
