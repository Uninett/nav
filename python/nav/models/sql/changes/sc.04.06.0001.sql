-- Create a table for interface aggregation information
CREATE TABLE manage.interface_aggregate (
  id SERIAL PRIMARY KEY, -- dummy primary key for Django
  aggregator INTEGER REFERENCES interface(interfaceid) ON DELETE CASCADE ON UPDATE CASCADE,
  interface INTEGER REFERENCES interface(interfaceid) ON DELETE CASCADE ON UPDATE CASCADE,
  UNIQUE (aggregator, interface)
);

CREATE INDEX interface_aggregate_aggregator ON interface_aggregate (aggregator);
CREATE INDEX interface_aggregate_interface ON interface_aggregate (interface);
