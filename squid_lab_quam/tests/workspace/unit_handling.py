import pint

if __name__ == "__main__":
    ureg = pint.UnitRegistry(auto_reduce_dimensions=True)
    # Set the default format to use the compact representation and add prefixes
    ureg.formatter.default_format = "~"

    # Define a frequency in Hz
    frequency_hz = 1000000000 * ureg.hertz  # 1 GHz in Hz

    # Convert to GHz
    frequency_ghz = frequency_hz.to(ureg.gigahertz)

    print(frequency_ghz)  # Output: 1.0 gigahertz
    print(frequency_hz)

    # Demonstrate compact representation
    print(frequency_hz.to_compact())

    # Convert and print expanded unit
    print(frequency_hz.to("MHz"))

    # Print using LaTeX
    from IPython.display import Latex, display

    ureg.formatter.default_format = "~L"
    display(Latex(f"$f = {frequency_hz.to_compact()}$"))
