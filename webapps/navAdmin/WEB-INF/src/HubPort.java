


class HubPort
{
	int unit;
	int port;
	String mac;

	public HubPort(int InUnit, int InPort, String InMac)
	{
		unit = InUnit;
		port = InPort;
		mac = InMac;
	}

	public int getUnit() { return unit; }
	public int getPort() { return port; }
	public String getMac() { return mac; }

}
