import java.awt.*;

class DrawAntiAlias
{
	public void drawAntiAliased(Graphics g, Polygon line, Color c)
	{
		Graphics2D g2 = (Graphics2D)g;
		g2.setColor(c);
		g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
		g2.fillPolygon(line);
		g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_OFF);
	}
}

