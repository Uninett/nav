-- Create index for ip column on manage.netbios to make lookups faster

CREATE INDEX netbios_ip ON manage.netbios (ip);
