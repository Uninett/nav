package no.ntnu.nav.getDeviceData.plugins;

import no.ntnu.nav.SimpleSnmp.*;

public interface DeviceHandler
{
	public boolean canHandleDevice(BoksData bd);
	public void handle(BoksData bd, SimpleSnmp sSnmp, DeviceDataList ddList) throws TimeoutException;

}