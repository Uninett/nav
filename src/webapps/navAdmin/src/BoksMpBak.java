/*
 * BoksMpBak.java
 *
 */
import java.util.*;

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
		calcKey();
	}

	public void setMp(String mp) {
		StringTokenizer st = new StringTokenizer(mp, ":");
		if (st.countTokens() != 2) throw new RuntimeException("Error in BoksMpBak.setMp: Malformed mp: " + mp);
		modulbak = st.nextToken();
		portbak = st.nextToken();
		calcKey();
	}

	public String hashKey() { return hashKey; }
	private void calcKey() { hashKey = boksbak+":"+modulbak+":"+portbak; }
	public String toString() {
		return "BoksMpBak [boksbak="+boksbak+", modulbak="+modulbak+", portbak="+portbak+"]";
	}
}
