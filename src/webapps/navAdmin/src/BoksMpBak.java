/*
 * BoksMpBak.java
 *
 */


public class BoksMpBak
{
	public Integer boksbak;
	public String modulbak;
	public String portbak;

	String hashKey;

	public BoksMpBak(int boksbak, String modulbak, String portbak)
	{
		this(new Integer(boksbak), modulbak, portbak);
	}
	public BoksMpBak(Integer boksbak, String modulbak, String portbak)
	{
		this.boksbak = boksbak;
		this.modulbak = modulbak;
		this.portbak = portbak;
		hashKey = boksbak+":"+modulbak+":"+portbak;
	}
	public String hashKey() { return hashKey; }
	public String toString() {
		return "BoksMpBak [boksbak="+boksbak+", modulbak="+modulbak+", portbak="+portbak+"]";
	}
}
