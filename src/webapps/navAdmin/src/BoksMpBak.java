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

	public void setToIfindex(String toIfindex) {
		this.toIfindex = toIfindex;
		calcKey();
	}

	public String hashKey() { return hashKey; }
	private void calcKey() { hashKey = boksbak+":"+toIfindex; }
	public String toString() {
		return "BoksMpBak [boksbak="+boksbak+", toIfindex="+toIfindex+"]";
	}
}
