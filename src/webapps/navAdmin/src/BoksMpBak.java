/*
 * BoksMpBak.java
 *
 */
import java.util.*;

public class BoksMpBak
{
	public Integer boksbak;
	public String toIfindex;

	String hashKey;

	public BoksMpBak(int boksbak, String toIfindex)
	{
		this(new Integer(boksbak), toIfindex);
	}

	public BoksMpBak(Integer boksbak, String toIfindex)
	{
		this.boksbak = boksbak;
		this.toIfindex = toIfindex;
		calcKey();
	}

	/*
	public void setMp(String mp) {
		StringTokenizer st = new StringTokenizer(mp, ":");
		if (st.countTokens() != 2) throw new RuntimeException("Error in BoksMpBak.setMp: Malformed mp: " + mp);
		modulbak = st.nextToken();
		portbak = st.nextToken();
		calcKey();
	}
	*/
	public void setToIfindex(String toIfindex) {
		this.toIfindex = toIfindex;
	}

	public String hashKey() { return hashKey; }
	private void calcKey() { hashKey = boksbak+":"+toIfindex; }
	public String toString() {
		return "BoksMpBak [boksbak="+boksbak+", toIfindex="+toIfindex+"]";
	}
}
