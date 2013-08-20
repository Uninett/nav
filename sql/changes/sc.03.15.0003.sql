-- Create a table for interface stacking information
CREATE TABLE manage.interface_stack (
  id SERIAL PRIMARY KEY, -- dummy primary key for Django
  higher INTEGER REFERENCES interface(interfaceid),
  lower INTEGER REFERENCES interface(interfaceid),
  UNIQUE (higher, lower)
);

CREATE INDEX interface_stack_higher ON interface_stack (higher);
CREATE INDEX interface_stack_lower ON interface_stack (lower);
