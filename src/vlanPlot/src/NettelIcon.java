/*
 * NTNU ITEA Nettnu prosjekt
 *
 * Skrvet av: Kristian Eide
 *
 */

import java.util.*;

import java.awt.*;
import java.awt.image.*;

class NettelIcon implements ImageObserver
{
	Com com;

	String imageName;
	static final String DIR_PREFIX = "common/";

	private int x;
	private int y;
	private int sizeX;
	private int sizeY;

	Image icon;
	Nettel parent;

	public NettelIcon(Com com, String kat, Nettel parent)
	{
		this.com = com;
		this.imageName = kat+".gif";
		this.parent = parent;

		if (!imageName.equals("gw.gif")) com.d("ImageName: " + imageName,2);

		// Hent ikonet
		if (com.getApplet() != null) {
			icon = com.getApplet().getImage(com.getApplet().getDocumentBase(),DIR_PREFIX+"icons/"+imageName);
		} else {
			icon = Toolkit.getDefaultToolkit().getImage(DIR_PREFIX+"icons/"+imageName);
		}
		sizeX = icon.getWidth(this);
		sizeY = icon.getHeight(this);
	}

	public boolean imageUpdate(Image img, int infoflags, int x, int y, int width, int height)
	{
		if ( (infoflags & ImageObserver.WIDTH) != 0) {
			sizeX = width;
		}

		if ( (infoflags & ImageObserver.HEIGHT) != 0) {
			sizeY = height;
		}

		if (sizeX != -1 && sizeY != -1) parent.recalcLink();

		return (sizeX == -1 || sizeY == -1);
	}

	public void setX(int x) { this.x = x; }
	public void setY(int y) { this.y = y; }
	public void setXY(int x, int y) { setX(x); setY(y); }


	public int getSizeX() { return sizeX; }
	public int getSizeY() { return sizeY; }

	public void drawSelf(Graphics g, Canvas c)
	{
		if (x < 10 || y < 10) com.d("Error ("+x+","+y+")",1);
		g.drawImage(icon, x, y, c);
	}

	public boolean contains(int x, int y)
	{
		Rectangle r = new Rectangle(this.x, this.y, sizeX, sizeY);
		return r.contains(x, y);
	}
}


/*
class NettelIcon
{
	public static final int LINK_ROUTER = 0;
	public static final int ELINK_ROUTER = 1;
	public static final int STAM_ROUTER = 2;
	public static final int LAN = 3;
	public static final int SWITCH = 4;
	public static final int KANT = 5;
	public static final int HUB = 6;
	public static final int SERVER = 7;
	public static final int MASKIN = 8;
	public static final int FEIL = 9;
	public static final int KOAKS = 10;
	public static final int UNDEF = 11;
	public static final int FIREWALL = 12;

	Com com;
	private Nettel nettel;
	private int type;
	private int x;
	private int y;
	private int sizeX;
	private int sizeY;

	boolean drawLast = false;

	Polygon[] poly = new Polygon[0];
	Color[] polyColor;
	boolean[] polyFill;

	Oval[] oval = new Oval[0];
	Color[] ovalColor;
	boolean[] ovalFill;

	Image[] icon = new Image[0];
	Dimension[] iconXY;





	public NettelIcon(Com InCom, Nettel InNettel, String s)
	{
		com = InCom;
		nettel = InNettel;

		if (s.equals("gw")) type = LINK_ROUTER;
		else if (s.equals("elink")) type = ELINK_ROUTER;
		else if (s.equals("stam")) type = STAM_ROUTER;
		else if (s.equals("lan")) type = LAN;
		else if (s.equals("sw")) type = SWITCH;
		else if (s.equals("kant")) type = KANT;
		else if (s.equals("hub")) type = HUB;
		else if (s.equals("srv")) type = SERVER;
		else if (s.equals("mas") || s.equals("pc") ) type = MASKIN;
		else if (s.equals("feil")) type = FEIL;
		else if (s.equals("koaks")) type = KOAKS;
		else if (s.equals("undef")) type = UNDEF;
		else if (s.equals("fw")) type = FIREWALL;
		else type = UNDEF;

	}

	public void drawSelf(Graphics g, int pass, Canvas c)
	{
		switch (pass)
		{
			case 2:
			{
				// tegn selve nettel-boxen med tekst og under-bokser
				for (int i = 0; i < poly.length; i++)
				{
					if (poly[i] != null)
					{
						g.setColor(polyColor[i]);
						if (polyFill[i])
						{
							g.fillPolygon(poly[i] );
						} else
						{
							g.drawPolygon(poly[i] );
						}
					}

					if (i < oval.length)
					{
						oval[i].drawSelf(g, ovalColor[i], ovalFill[i] );
					}

					if (i < icon.length)
					{
						g.drawImage(icon[i], iconXY[i].width, iconXY[i].height, c);
					}



				}

				for (int i = poly.length; i < oval.length; i++)
				{
					oval[i].drawSelf(g, ovalColor[i], ovalFill[i] );
				}

				for (int i = poly.length; i < icon.length; i++)
				{
					g.drawImage(icon[i], iconXY[i].width, iconXY[i].height, c);
				}



			}
			break;



		}




	}

	public boolean contains(int InX, int InY)
	{
		Rectangle r = new Rectangle(x, y, sizeX, sizeY);
		return r.contains(InX, InY);
	}


	public void setXY(int InX, int InY)
	{
		x = InX;
		y = InY;

		switch (type)
		{
			case LINK_ROUTER:
				calcLinkRouter();
			break;

			case ELINK_ROUTER:
				calcELinkRouter();
			break;

			case STAM_ROUTER:
				calcStamRouter();
			break;

			case LAN:
				calcLAN();
			break;

			case SWITCH:
				calcSwitch();
			break;

			case KANT:
				calcKant();
			break;

			case HUB:
				calcHUB();
			break;

			case SERVER:
				calcServer();
			break;

			case MASKIN:
				calcMaskin();
			break;

			case UNDEF:
				calcUndef();
			break;

			case FIREWALL:
				calcFirewall();
			break;


			default:
				//calcBasicNettel();
			break;
		}

	}

	private void calcLinkRouter()
	{
		sizeX = 45;
		sizeY = 26;

		icon = new Image[1];
		iconXY = new Dimension[1];
		iconXY[0] = new Dimension(x, y);

		if (com.getApplet() != null)
		{
			icon[0] = com.getApplet().getImage(com.getApplet().getDocumentBase(),"icons/router.gif");
		} else
		{
			icon[0] = Toolkit.getDefaultToolkit().getImage("icons/router.gif");
		}

		drawLast = true;
	}

	private void calcELinkRouter()
	{
		sizeX = 45;
		sizeY = 26;

		icon = new Image[1];
		iconXY = new Dimension[1];
		iconXY[0] = new Dimension(x, y);

		if (com.getApplet() != null)
		{
			icon[0] = com.getApplet().getImage(com.getApplet().getDocumentBase(),"icons/elink.gif");
		} else
		{
			icon[0] = Toolkit.getDefaultToolkit().getImage("icons/elink.gif");
		}

		drawLast = false;
	}

	private void calcStamRouter()
	{
		sizeX = 45;

		icon = new Image[1];
		iconXY = new Dimension[1];
		iconXY[0] = new Dimension(x, y);

		if (nettel.getName().equals("fddi"))
		{
			if (com.getApplet() != null)
			{
				icon[0] = com.getApplet().getImage(com.getApplet().getDocumentBase(),"icons/fddi.gif");
			} else
			{
				icon[0] = Toolkit.getDefaultToolkit().getImage("icons/fddi.gif");
			}
			sizeY = 19;
		} else
		{
			if (com.getApplet() != null)
			{
				icon[0] = com.getApplet().getImage(com.getApplet().getDocumentBase(),"icons/stam.gif");
			} else
			{
				icon[0] = Toolkit.getDefaultToolkit().getImage("icons/stam.gif");
			}
			sizeY = 27;
		}

		drawLast = false;
	}

	private void calcLAN()
	{
		sizeX = 45;
		sizeY = 27;

		icon = new Image[1];
		iconXY = new Dimension[1];
		iconXY[0] = new Dimension(x, y);

		if (com.getApplet() != null)
		{
			icon[0] = com.getApplet().getImage(com.getApplet().getDocumentBase(),"icons/lan.gif");
		} else
		{
			icon[0] = Toolkit.getDefaultToolkit().getImage("icons/lan.gif");
		}

		drawLast = false;
	}

	private void calcSwitch()
	{
		sizeX = 45;
		sizeY = 30;

		icon = new Image[1];
		iconXY = new Dimension[1];
		iconXY[0] = new Dimension(x, y);

		if (com.getApplet() != null)
		{
			icon[0] = com.getApplet().getImage(com.getApplet().getDocumentBase(),"icons/switch.gif");
		} else
		{
			icon[0] = Toolkit.getDefaultToolkit().getImage("icons/switch.gif");
		}

		drawLast = true;
	}

	private void calcKant()
	{
		sizeX = 45;
		sizeY = 25;

		icon = new Image[1];
		iconXY = new Dimension[1];
		iconXY[0] = new Dimension(x, y);

		if (com.getApplet() != null)
		{
			icon[0] = com.getApplet().getImage(com.getApplet().getDocumentBase(),"icons/snmphub.gif");
		} else
		{
			icon[0] = Toolkit.getDefaultToolkit().getImage("icons/snmphub.gif");
		}

		drawLast = false;
	}

	private void calcHUB()
	{
		sizeX = 45;
		sizeY = 18;

		icon = new Image[1];
		iconXY = new Dimension[1];
		iconXY[0] = new Dimension(x, y);

		if (com.getApplet() != null)
		{
			icon[0] = com.getApplet().getImage(com.getApplet().getDocumentBase(),"icons/hub.gif");
		} else
		{
			icon[0] = Toolkit.getDefaultToolkit().getImage("icons/hub.gif");
		}

		drawLast = false;
	}

	private void calcServer()
	{
		sizeX = 45;
		sizeY = 34;

		icon = new Image[1];
		iconXY = new Dimension[1];
		iconXY[0] = new Dimension(x, y);

		if (com.getApplet() != null)
		{
			icon[0] = com.getApplet().getImage(com.getApplet().getDocumentBase(),"icons/server.gif");
		} else
		{
			icon[0] = Toolkit.getDefaultToolkit().getImage("icons/server.gif");
		}

		drawLast = false;
	}

	private void calcMaskin()
	{
		sizeX = 45;
		sizeY = 39;

		icon = new Image[1];
		iconXY = new Dimension[1];
		iconXY[0] = new Dimension(x, y);

		if (com.getApplet() != null)
		{
			icon[0] = com.getApplet().getImage(com.getApplet().getDocumentBase(),"icons/maskin.gif");
		} else
		{
			icon[0] = Toolkit.getDefaultToolkit().getImage("icons/maskin.gif");
		}

		drawLast = false;
	}

	private void calcUndef()
	{
		sizeX = 45;
		sizeY = 26;

		icon = new Image[1];
		iconXY = new Dimension[1];
		iconXY[0] = new Dimension(x, y);

		if (com.getApplet() != null)
		{
			icon[0] = com.getApplet().getImage(com.getApplet().getDocumentBase(),"icons/undef.gif");
		} else
		{
			icon[0] = Toolkit.getDefaultToolkit().getImage("icons/undef.gif");
		}

		drawLast = false;
	}

	private void calcFirewall()
	{
		sizeX = 45;
		sizeY = 26;

		icon = new Image[1];
		iconXY = new Dimension[1];
		iconXY[0] = new Dimension(x, y);

		if (com.getApplet() != null)
		{
			icon[0] = com.getApplet().getImage(com.getApplet().getDocumentBase(),"icons/fw.gif");
		} else
		{
			icon[0] = Toolkit.getDefaultToolkit().getImage("icons/fw.gif");
		}

		drawLast = false;
	}



	private void calcBasicNettel2()
	{
		//////////////////////
		// Config

			int sizeX = 45;
			int sizeY = 20;
			int FONT_SIZE = 9;
			Font nf = new Font("Helvetica",Font.PLAIN, FONT_SIZE);

			int canvasTopSpaceY = 25; // plass til overskrift

			int topSpace = 0;
			int leftSpace = 3;
			int rightSpace = 2;
			int bottomSpace = 10;

			int vlanBoxSizeX = 24;
			int vlanBoxSizeY = 12;

			int lastBoxDivider = 4;
			int lastBoxSpaceX = 4;
			int lastBoxSpaceY = 2;
		//////////////////////////

		this.sizeX = sizeX;
		this.sizeY = sizeY;

		Polygon nettelPoly;
		Polygon nettelPolyLast;

		{ // selve nettel-boxen
			nettelPoly = new Polygon();
			nettelPoly.addPoint(x, y);
			nettelPoly.addPoint(x+sizeX, y);
			nettelPoly.addPoint(x+sizeX, y+sizeY);
			nettelPoly.addPoint(x, y+sizeY);
		}

		{ // box for CPU-last / bakplan-last
			int lastSizeX = sizeX/lastBoxDivider;
			int lastSizeY = sizeY/lastBoxDivider;
			int fromX = x+sizeX/2-lastSizeX/2;
			int fromY = y+sizeY-lastSizeY-lastBoxSpaceY;

			nettelPolyLast = new Polygon();
			nettelPolyLast.addPoint(fromX, fromY);
			nettelPolyLast.addPoint(fromX+lastSizeX, fromY);
			nettelPolyLast.addPoint(fromX+lastSizeX, fromY+lastSizeY);
			nettelPolyLast.addPoint(fromX, fromY+lastSizeY);
		}

		poly = new Polygon[4];
		poly[0] = nettelPoly;
		poly[1] = nettelPoly;
		poly[2] = nettelPolyLast;
		poly[3] = nettelPolyLast;

		polyColor = new Color[4];
		polyColor[0] = Color.black;
		polyColor[1] = Color.lightGray;
		polyColor[2] = Color.black;

		// Nettel-bokser skal alltid farges relativt
		LastColor.setTmpSkala(LastColor.RELATIV_SKALA);
		polyColor[3] = LastColor.getColor(nettel.nettelLastPst);
		LastColor.unsetTmpSkala();

		polyFill = new boolean[4];
		polyFill[0] = false;
		polyFill[1] = true;
		polyFill[2] = false;
		polyFill[3] = true;



	}


	public int getSizeX() { return sizeX; }
	public int getSizeY() { return sizeY; }
	public boolean getDrawLast() { return drawLast; }





}
*/

























