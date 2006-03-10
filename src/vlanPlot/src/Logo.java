import java.awt.Color;
import java.awt.Graphics;
import java.awt.Image;
import java.awt.Canvas;

class Logo extends Canvas
{
	Com com;
	Image navLogo;
	static final String DIR_PREFIX = "gfx/";

	public Logo(Com InCom)
	{
		com = InCom;

		Mouse mouse = new Mouse(com);
		MouseMove mv = new MouseMove(com);
		addMouseListener(mouse);
		addMouseMotionListener(mv);
		setSize(100, 232);


	}

	public void paint(Graphics g)
	{

		// Linjer
		{
			int xstart = 20;
			int ystart = 8;

		    // Tykkelse på linjer
		    g.setColor(Color.black);
		    g.fillRect(xstart,ystart,30,3);
		    g.fillRect(xstart,ystart+9,30,5);
		    g.fillRect(xstart,ystart+20,30,8);

			// tekst
			g.drawString("<10Mb", xstart+35, ystart+7);
			g.drawString("<100Mb", xstart+35, ystart+17);
			g.drawString("<1Gb", xstart+35, ystart+28);
		}

	    // Fargeskala
	    int xstart = 10;
	    int ystart = 52;
	    int boxSizeX = 15;
	    int boxSizeY = 15;
	    int spaceX = 5;

	    for (int i = LastColor.getAntTrinn()-1; i >= 0; i--)
	    {
		    g.setColor(LastColor.getColorTrinn(i) );
		    g.fillRect(xstart,ystart,boxSizeX,boxSizeY);

		    g.setColor(Color.black);
		    g.drawRect(xstart,ystart,boxSizeX,boxSizeY);

		    g.drawString(LastColor.getStringTrinn(i) ,xstart+boxSizeX+spaceX, ystart+10);

			ystart += boxSizeY;
		}


	}
}

