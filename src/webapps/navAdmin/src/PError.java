class PError extends Throwable
{
	public PError(String InMsg)
	{
		msg = InMsg;
	}

	public PError(String InMsg, String[] InS)
	{
		msg = InMsg;
		s = InS;

	}

	public String msg()
	{
		return msg;
	}

	public String getError()
	{
		return msg;
	}

	public String[] getData()
	{
		return s;
	}

	String msg;
	String[] s;
}