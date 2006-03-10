/*
 * NTNU ITEA Nettnu prosjekt
 *
 * Skrvet av: Kristian Eide
 *
 */

import java.util.*;

import java.awt.*;
import java.awt.event.*;

class LayoutXY
{
	// konfigurasjon UPLINK og DNLINK
	int vtDivider = 16; // mellomrom mellom kanten og boksene
	int spaceX = 30; // mellomrom mellom selve boksene

	// konfigurasjon HZLINK
	int hzDivider = 32;
	int spaceY = 20;


	Com com;
	String linkType;

	// statiske konstanter
	public static final int UPLINK = 0;
	public static final int HZLINK = 1;
	public static final int DNLINK = 2;

	int canvasX, canvasY;
	int sizeX, sizeY;
	int retX, retY;
	int borderVt, borderHz;

	int total;
	int current = 1;

	public LayoutXY(Com InCom, String InLinkType, int InTotal)
	{
		com = InCom;
		linkType = InLinkType;
		total = InTotal;

		canvasX = com.getNet().getMinimumSize().width;
		canvasY = com.getNet().getMinimumSize().height;

		sizeX = Nettel.sizeX;
		sizeY = Nettel.sizeY;

		borderVt = canvasY / vtDivider;
		borderHz = canvasX / hzDivider;

		if (linkType.equals("up") || linkType.equals("dn") )
		{
			calcVt();
		}
	}

	public void reset()
	{
		current = 1;
	}


	public int[] getXY()
	{
		if (linkType.equals("up") || linkType.equals("dn") )
		{
			return getVt();

		} else
		if (linkType.equals("hz"))
		{
			return getHz();
		}

		return new int[0];
	}

	public int getTotal() { return total; }

	public int getAntVisible()
	{
		if (linkType.equals("up") || linkType.equals("dn") )
		{
			return (canvasX - borderVt*2) / (Nettel.sizeX+spaceX);

		} else
		if (linkType.equals("hz") )
		{
			int availY = canvasY - borderVt*2 - (int)((Nettel.sizeY+spaceY)*2*1.5);
			int visible = availY / (Nettel.sizeY+spaceY);

			return visible*2;
		}
		return 0;
	}

	private void calcVt()
	{
		if (linkType.equals("up"))
		{
			retY = borderVt;

		} else
		if (linkType.equals("dn"))
		{
			retY = canvasY - borderVt;
			retY -= Nettel.sizeY;
		}
	}

	private int[] getVt()
	{
		retX = canvasX/2 - (Math.min(getTotal(), getAntVisible()) * (Nettel.sizeX+spaceX))/2 + spaceX/2;
		retX += (Nettel.sizeX+spaceX)*(current-1);

		current++;

		int[] ret = new int[2];
		ret[0] = retX;
		ret[1] = retY;

		return ret;
	}

	private int[] getHz()
	{
		// oddetall, boxen settes på venstre side
		// partall, boxen settes på høyre side
		int retX = ((current&1)!=0) ? borderHz : canvasX - borderHz - Nettel.sizeX;

		int antRader = (Math.min(getTotal(), getAntVisible() )+1)/2;
		retY = canvasY/2 - antRader*(Nettel.sizeY+spaceY)/2 + spaceY/2;

		// kun øk Y-verdi dersom oddetall
		int t = current;
		if ((t&1)==0) t--;
		retY += (Nettel.sizeY+spaceY)* ((t-1)/2);

		current++;

		int[] ret = new int[2];
		ret[0] = retX;
		ret[1] = retY;

		return ret;
	}


/*
	private void calcVt()
	{
		if (borderX + (sizeX+spaceX) * total > canvasX)
		{
			layers = (borderX + (sizeX+spaceX)) * total / canvasX + 1;
			prLayer = total / layers;

			if (total/layers*layers != total)
			{
				prLayer += 1;
			}

		}

		if (link == UPLINK)
		{
			retY = canvasY / borderDivider;

		} else
		if (link == DNLINK)
		{
			retY = (int) (canvasY * (1.0 - 1.0/(float)borderDivider) );
			retY -= Nettel.sizeY;
		}
	}
*/

/*
	private void calcHz()
	{
		int availableX = canvasX - Nettel.sizeX*3 - borderX*2;

		if ((sizeX+spaceX) * total > availableX)
		{
			layers = (sizeX+spaceX) * total / availableX + 1;
			prLayer = total / layers;

			if (total/layers*layers != total)
			{
				prLayer += 1;
			}

			// sørg for partall prLayer
			if ( (prLayer/2)*2 != prLayer)
			{
				// oddetall, fix
				prLayer--;
				layers = total / prLayer;

				if (total/prLayer*prLayer != total)
				{
					layers += 1;
				}
			}

		}

		retY = canvasY/2 - sizeY/2;
		retY -= (hzSpaceY+sizeY)*(layers-1) / 2;

		com.d("calcHz, availX: " + availableX + " layers: " + layers + " prLayer: " + prLayer, 6);

	}
*/



/*
	private void checkNextLayerVt()
	{
		if (tellerX > prLayer)
		{
			// X-koordinat
			tellerX = 1;
			tellerY++;

			// Y-koordinat
			if (link == UPLINK)
			{
				//retY += tellerY*(Nettel.sizeY+spaceY);
				retY += (Nettel.sizeY+spaceY);
			} else
			if (link == DNLINK)
			{
				//retY -= tellerY*(Nettel.sizeY+spaceY);
				retY -= (Nettel.sizeY+spaceY);
			}
		}

	}
*/
/*
	private void checkNextLayerHz()
	{

		if (tellerX > prLayer)
		{
			// X-koordinat
			tellerX = 1;
			tellerY++;

			retY += (sizeY+hzSpaceY);

		}

	}
*/

/*
	private int[] getHz()
	{
		if ( (tellerX/2)*2 != tellerX)
		{
			// oddetall, boks på venstre side

			//retX = canvasX*(tellerX/2+1)/(prLayer+1) - Nettel.sizeX/2;

			retX = borderX+(spaceX+sizeX)*(tellerX/2);


		} else
		{
			// partall, boks på høyre side
			//retX = canvasX*(tellerX/2)/(prLayer+1) - Nettel.sizeX/2;
			//retX = canvasX - retX - Nettel.sizeX;

			retX = borderX+(spaceX+sizeX)*((tellerX-1)/2);
			retX = canvasX - retX - sizeX;

		}

		com.d("   XY: " + teller + " av " + total + ", " + tellerX + " av " + prLayer + ", lag: " + tellerY + " antLag: " + (total/prLayer+1), 6);
		com.d("   retX: " + retX + ", retY: " + retY + " canvasX: " + canvasX + " canvasY: " + canvasY, 6);


		tellerX++;
		teller++;

		int[] ret = new int[2];
		ret[0] = retX;
		ret[1] = retY;

		return ret;

	}
*/







}



























