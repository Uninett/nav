package no.ntnu.nav.getDeviceData.plugins;

/**
 * <p>
 * Interface for returning the data collected from a device.
 * </p>
 *
 * <p>
 * Plugin modules must construct new objects describing the collected data
 * (e.g. SwportData objects for describing switch ports); this is done in the
 * normal manner using the "new" operator. Then the objects are added by
 * calling the appropriate add method of this interface.
 * </p>
 *
 */
public interface DeviceDataList
{

	public void setDeviceData(DeviceData deviceData);
	public void addSwportData(SwportData swportData);
}
