/*
 * NTNU ITEA Nettnu prosjekt
 *
 * Skrvet av: Kristian Eide
 *
 */

import java.util.*;

import java.awt.*;
import java.awt.event.*;

class Link
{
	public static int LESS_0_MBIT = 3;
	public static int LESS_10_MBIT = 7;
	public static int LESS_100_MBIT = 11;
	public static int LESS_1000_MBIT = 15;
	public static int MORE_1000_MBIT = 19;
	public static int POPUP_WIDTH = 19;

	private static final Color BLOCKED_LINE_COLOR = Color.red;
	private static final int BLOCKED_LINE_LENGTH = 14;
	private static final int BLOCKED_LINE_WIDTH = 10;

	Nettel to;
	Nettel from;
	int linkId;
	Polygon line;
	Polygon border;
	Polygon popupLine;
	double capacity;
	double last = -1;
	double lastPst = -1;
	Color color;
	String ifName;
	String ospf = null;

	// Angir om linken er blokkert (av spanning tree)
	boolean isBlocked = false;
	boolean drawBlocked = false;
	Polygon blockedLine;

	// Only with Java 1.2+
	boolean graphics2DSupport = false;
	DrawAntiAlias drawAntiAlias = null;


	// Hver link har sin egen PopupMessage
	Hashtable keywords = new Hashtable();
	PopupMessage activePopup;
	PopupMessage desc;
	String descText;

	// Brukes for å sjekke om muspekeren er over en vlan-boks på en link
	Rectangle vlanRect = new Rectangle();
	PopupMessage vlanDesc;
	Vector vlanList = new Vector();
	boolean allVlansEqual = true;

	boolean isVisible = true;

	public Link(Nettel InFrom, Nettel InTo, int InLinkId, double InCapacity, double InLast, String ifName)
	{
		from = InFrom;
		to = InTo;
		linkId = InLinkId;
		capacity = InCapacity;
		setLast(InLast);
		this.ifName = ifName;

		if (Com.javaMajorVersion > 1 || Com.javaMinorVersion >= 2) graphics2DSupport = true;

		keywords.put("linkId".toLowerCase(), String.valueOf(linkId));
		keywords.put("sysNameFrom".toLowerCase(), from.getName());
		keywords.put("sysNameTo".toLowerCase(), to.getName());
		keywords.put("speed".toLowerCase(), Double.toString(capacity));
		keywords.put("interface".toLowerCase(), ifName);

		recalc();

	}

	public void setLast(double InLast)
	{
		if (capacity <= 0) return;

		last = InLast;
		lastPst = (InLast*8) / (capacity*1024*1024) * 100; // input er i bytes

		String lastPstS = (lastPst >= 0.01) ? LastColor.format(lastPst,2)+"%" : "<0.01%";
		String lastS = (last > 0) ? LastColor.formatBytes(last*8,true,2,true) : "No data";

		keywords.put("LinkLastPst".toLowerCase(), lastPstS);
		keywords.put("LinkLast".toLowerCase(), lastS);
	}

	public void setVlanRect(Rectangle r)
	{
		vlanRect = r;
	}

	public boolean contains(int x, int y)
	{
		if (!isVisible()) return false;

		if (vlanRect.contains(x, y)) return true;
		return popupLine.contains(x, y);
	}

	public String getType()
	{
		if (from.getKat().equals("gw") ||
			from.getKat().equals("lan") ||
			from.getKat().equals("stam") ||
			from.getKat().equals("elink") )
		{
			return "net";
		}
		return "sw";
	}

	public void setIsBlocked(boolean b) { isBlocked = b; }
	public void setDrawBlocked(boolean b) { drawBlocked = b; }

	public int getId() { return linkId; }
	public double getCapacity() { return capacity; }
	public double getLast() { return last; }
	public double getLastPst() { return lastPst; }
	public String getIfName() { return ifName; }
	public Nettel getNettelTo() { return to; }

	public Link getLinkOtherWay()
	{
		return to.getLinkTo(from);
	}

	// OSPF
	/*
	public void setOspf(String s) { ospf = s; }
	public String getOspf()
	{
		if (ospf == null) return null;
		if (ospf.equals("0")) return "OSPF cost: NA";

		return "OSPF cost: " + ospf;
	}
	*/

	// Metoder for IP adresse-rom
	/*
	public void addIpRom(String gwip, String bits, String maxhosts, String antmask)
	{
		ipRom.addElement(gwip + "," + bits + "," + maxhosts + "," + antmask);
	}
	public String getIpRom()
	{
		if (ipRom.size() == 0)
		{
			return null;
		}
		String ipRomString = "IP address-space:\n";
		for (int i = 0; i < ipRom.size(); i++)
		{
			String s = (String)ipRom.elementAt(i);
			String gwip = (misc.tokenize(s, ","))[0];
			String bits = (misc.tokenize(s, ","))[1];
			String maxhosts = (misc.tokenize(s, ","))[2];
			String antmask = (misc.tokenize(s, ","))[3];

			s = "  " + gwip + "/" + bits + ", in use: " + antmask + "/" + maxhosts;
			if (i != 0)
			{
				ipRomString += "\n";
			}
			ipRomString += s;
		}
		return ipRomString;
	}
	public Vector getIpRomV()
	{
		if (ipRom.size() == 0) return new Vector();
		Vector v = new Vector();

		for (int i = 0; i < ipRom.size(); i++)
		{
			String s = (String)ipRom.elementAt(i);
			String gwip = (misc.tokenize(s, ","))[0];
			String bits = (misc.tokenize(s, ","))[1];

			s = gwip + "/" + bits;
			v.addElement(s);
		}
		return v;
	}
	*/

	public PopupMessage showPopup(int x, int y, Graphics g, Com com)
	{
		activePopup = (vlanDesc != null && vlanRect.contains(x, y)) ? vlanDesc : desc;
		if (activePopup != null) {
			com.d("    Showing popup at ("+x+","+y+")",8);
			activePopup.show(x, y, g);
		} else {
			com.d("    Cannot show popup at ("+x+","+y+"), pm is null",8);
		}
		return activePopup;
	}
	public void hidePopup()
	{
		if (desc != null) desc.hide();
		if (vlanDesc != null) vlanDesc.hide();
	}
	public void updatePopup(Canvas notify, Font popupFont)
	{
		desc = new PopupMessage(notify, popupFont);
		if (descText != null) desc.addMessage(descText);

		if (vlanList.size() > 1 && !allVlansEqual) {
			vlanDesc = new PopupMessage(notify, popupFont);
			for (int i=0; i < vlanList.size(); i++) {
				//Integer vlan = (Integer)vlanList.elementAt(i);
				//vlanDesc.addMessage(String.valueOf(vlan));
				String vlan = (String)vlanList.elementAt(i);
				vlanDesc.addMessage(vlan);
			}
		} else {
			vlanDesc = null;
		}
	}

	public String processText(String text, String[] data)
	{
		descText = Input.processText(text, data, keywords);
		return descText;
	}

	public boolean isVisible() { return isVisible && from.isVisible() && to.isVisible(); }
	public void setVisible(boolean b) { isVisible = b; }

	public void addVlan(String vlan) {
		vlanList.addElement(vlan);
		// Litt mer komplisert kode fordi hvis all vlan er like så skal vi ikke behandle linken som en trunk
		if (allVlansEqual && vlanList.size() > 1) {
			if (!((String)vlanList.elementAt(0)).equals(vlan)) allVlansEqual = false;
		}

	}
	public boolean getIsTrunk() { return vlanList.size() > 1 && !allVlansEqual; }

	public void drawSelf(Graphics g)
	{
		if (!isVisible()) return;
		//if (capacity >= 1000)
		//{
		//	g.setColor(Color.black);
		//	g.fillPolygon(border);
		//}

		/*
		g.setColor(color);
		g.fillPolygon(line);
		*/
		if (graphics2DSupport) {
			if (drawAntiAlias == null) drawAntiAlias = new DrawAntiAlias();
			drawAntiAlias.drawAntiAliased(g, line, color);
			if (blockedLine != null) drawAntiAlias.drawAntiAliased(g, blockedLine, BLOCKED_LINE_COLOR);
		} else {
			// Not JDK 1.2+ :(
			g.setColor(color);
			g.fillPolygon(line);
			if (blockedLine != null) {
				g.setColor(BLOCKED_LINE_COLOR);
				g.fillPolygon(blockedLine);
			}
		}

	}
	public void drawPopup(Graphics g)
	{
		if (activePopup != null) activePopup.drawSelf(g);
	}


	public void recalc()
	{
		if (!isVisible()) return;

		int fromX = from.getX() + from.getSizeX()/2;
		int fromY = from.getY() + from.getSizeY()/2;
		int toX = to.getX() + to.getSizeX()/2;
		int toY = to.getY() + to.getSizeY()/2;

		double linjekap;
		if (capacity <= 0)
		{
			linjekap = LESS_0_MBIT;
		} else
		if (capacity <= 10)
		{
			linjekap = LESS_10_MBIT; // <=10mbit
		} else
		if (capacity <= 100)
		{
			linjekap = LESS_100_MBIT; // <=100mbit
		} else
		if (capacity <= 1000)
		{
			linjekap = LESS_1000_MBIT; // <=1000mbit
		} else
		{
			linjekap = MORE_1000_MBIT; // 1000> mbit
		}

		double useLast = (LastColor.getSkala() == LastColor.RELATIV_SKALA) ? lastPst : last*8;
		if (isBlocked) {
			color = Color.gray;
			if (drawBlocked) blockedLine = calcBlockedLine(fromX, fromY, toX, toY, BLOCKED_LINE_LENGTH, BLOCKED_LINE_WIDTH);
		} else {
			color = LastColor.getColor(useLast);
		}

		line = calcLine(fromX, fromY, toX, toY, linjekap);
		//border = calcLine(fromX, fromY, toX, toY, linjekap+5);
		popupLine = calcLine(fromX, fromY, toX, toY, POPUP_WIDTH);
	}


	private Polygon calcLine(int x1, int y1, int x2, int y2, double width)
	{
		Polygon p = new Polygon();

		double xm = (x1+x2)/2;
		double ym = (y1+y2)/2;

		// Vektoren fra x1,y1 til xm,ym
		double vx = xm-x1;
		double vy = ym-y1;

		double tl = (width/4) / Math.sqrt(Math.pow(vx,2) + Math.pow(vy,2));
		double dxw = vy * tl;
		double dyw = -(vx * tl);

		p.addPoint((int)(x1+dxw), (int)(y1+dyw));
		p.addPoint((int)(x1-dxw), (int)(y1-dyw));

		p.addPoint((int)(x1-dxw + vx), (int)(y1-dyw + vy));
		p.addPoint((int)(x1+dxw + vx), (int)(y1+dyw + vy));

		return p;
	}


	/*
	private Polygon calcLine_old(int x1, int y1, int x2, int y2, double width)
	{
		Polygon p = new Polygon();

		// sjekk om denne boksen er nærmest 0,0
		boolean b = false;
		if (x1+y1 < x2+y2) {
			b = true;
		} else
		if (x1+y1 == x2+y2) {
			if (x1 < x2) {
				b = true;
			}
		}

		if (b) {
			int tx, ty;

			tx = x2;
			ty = y2;

			x2 = x1;
			y2 = y1;

			x1 = tx;
			y1 = ty;
		}

		double deltax,deltay,alfa,beta;

	    alfa = Math.atan(((double)(y2-y1)/(double)(x2-x1)));
	    beta = Math.PI/2. - alfa;

	    deltax = (Math.cos(beta)*(double)width)/2.;
	    deltay = (Math.sin(beta)*(double)width)/2.;


	    int xm = (x2-x1)/2 +x1;
	    int ym = (y2-y1)/2 +y1;


		if (b) {
			int xt = x2-x1;
			int yt = y2-y1;

		    p.addPoint(x1+(int)deltax + xt,y1-(int)deltay + yt);
		    p.addPoint(xm+(int)deltax,ym-(int)deltay);

		    p.addPoint(xm,ym);
		    p.addPoint(x1 + xt,y1 + yt);
		} else {
		    p.addPoint(x1+(int)deltax,y1-(int)deltay);
		    p.addPoint(xm+(int)deltax,ym-(int)deltay);

		    p.addPoint(xm,ym);
		    p.addPoint(x1,y1);
		}


		return p;
	}
	*/

	private Polygon calcBlockedLine(int x1, int y1, int x2, int y2, double length, double width)
	{
		Polygon p = new Polygon();

		// Trenger punkt 2/7 ut på linjen
		double xp = 2*(x2-x1)/7.0 + x1;
		double yp = 2*(y2-y1)/7.0 + y1;

		// Lager en vektor som står vinkelrett på linjen fra x1,y1 til x2,y2 ved å snu
		// koordinatene. Deretter endres lengden på vektoren til width/2

		// Vektoren fra xp,yp til x2,y2
		double vx = x2-xp;
		double vy = y2-yp;

		double tl = (length/2) / Math.sqrt(Math.pow(vx,2) + Math.pow(vy,2));
		double dxl = vy * tl;
		double dyl = -(vx * tl);

		double tw = (width/2) / Math.sqrt(Math.pow(vx,2) + Math.pow(vy,2));
		double dxw = vx * tw;
		double dyw = vy * tw;

		p.addPoint((int)(xp+dxl - dxw), (int)(yp+dyl - dyw));
		p.addPoint((int)(xp-dxl - dxw), (int)(yp-dyl - dyw));

		p.addPoint((int)(xp-dxl + dxw), (int)(yp-dyl + dyw));
		p.addPoint((int)(xp+dxl + dxw), (int)(yp+dyl + dyw));

		return p;
	}

}