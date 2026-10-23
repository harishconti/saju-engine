import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { DateOfBirthField } from "../date-of-birth-field";
import { TimeOfBirthField } from "../time-of-birth-field";

/**
 * The reported bugs (2026-10-22):
 *
 *  1. the date field accepted **today's** date — a reading for a baby. The server now refuses it
 *     (`lib/birth.ts`); the field shows the same rule and echoes the date it understood;
 *  2. the date and time fields **could not be typed into** on a phone (a native date/time input
 *     is a wheel picker there), and a typed "19/03/1993" was silently rejected.
 *
 * So the fields are text inputs that parse what people type, and they say what they read.
 */
describe("DateOfBirthField", () => {
  it("accepts a date typed as DD/MM/YYYY and echoes what it understood", () => {
    const onChange = vi.fn();
    render(<DateOfBirthField value="" onChange={onChange} />);
    const input = screen.getByLabelText("Date of birth") as HTMLInputElement;

    fireEvent.change(input, { target: { value: "19/03/1993" } });
    fireEvent.blur(input);

    expect(onChange).toHaveBeenCalledWith("1993-03-19");
  });

  it("accepts YYYY-MM-DD too", () => {
    const onChange = vi.fn();
    render(<DateOfBirthField value="" onChange={onChange} />);
    const input = screen.getByLabelText("Date of birth") as HTMLInputElement;

    fireEvent.change(input, { target: { value: "1993-03-19" } });
    fireEvent.blur(input);

    expect(onChange).toHaveBeenCalledWith("1993-03-19");
  });

  it("shows the date it read, so a misread is visible", () => {
    render(<DateOfBirthField value="1993-03-19" onChange={vi.fn()} />);
    expect(screen.getByText(/19 March 1993/)).toBeTruthy();
  });

  it("refuses a date inside the last year, with the one-year message", () => {
    const today = new Date().toISOString().slice(0, 10);
    render(<DateOfBirthField value={today} onChange={vi.fn()} />);
    expect(screen.getByText(/Readings start at 1 year old/)).toBeTruthy();
  });

  it("keeps a native date picker behind the calendar button", () => {
    render(<DateOfBirthField value="" onChange={vi.fn()} />);
    expect(screen.getByLabelText("Open the calendar")).toBeTruthy();
  });

  it("fills the text box when the date comes from the calendar picker", () => {
    const onChange = vi.fn();
    const { container } = render(<DateOfBirthField value="" onChange={onChange} />);
    const native = container.querySelector('input[type="date"]') as HTMLInputElement;

    fireEvent.change(native, { target: { value: "1990-07-04" } });

    expect(onChange).toHaveBeenCalledWith("1990-07-04");
    expect((screen.getByLabelText("Date of birth") as HTMLInputElement).value).not.toBe("");
  });

  it("clears the committed date when the box is emptied or mistyped, so a stale date is never sent", () => {
    const onChange = vi.fn();
    render(<DateOfBirthField value="1993-03-19" onChange={onChange} />);
    const input = screen.getByLabelText("Date of birth") as HTMLInputElement;

    fireEvent.change(input, { target: { value: "19/03/19" } });
    fireEvent.blur(input);

    expect(onChange).toHaveBeenCalledWith("");
  });
});

describe("TimeOfBirthField", () => {
  it("accepts a time typed as 2:30 pm and echoes what it understood", () => {
    const onChange = vi.fn();
    render(<TimeOfBirthField value="" onChange={onChange} />);
    const input = screen.getByLabelText("Time of birth") as HTMLInputElement;

    fireEvent.change(input, { target: { value: "2:30 pm" } });
    fireEvent.blur(input);

    expect(onChange).toHaveBeenCalledWith("14:30");
  });

  it("accepts a 24-hour time", () => {
    const onChange = vi.fn();
    render(<TimeOfBirthField value="" onChange={onChange} />);
    const input = screen.getByLabelText("Time of birth") as HTMLInputElement;

    fireEvent.change(input, { target: { value: "14:30" } });
    fireEvent.blur(input);

    expect(onChange).toHaveBeenCalledWith("14:30");
  });

  it("shows the time it read, so 2:30 is never silently 14:30", () => {
    render(<TimeOfBirthField value="14:30" onChange={vi.fn()} />);
    expect(screen.getByText(/2:30 PM/)).toBeTruthy();
  });
  it("fills the text box when the time comes from the clock picker", () => {
    const onChange = vi.fn();
    const { container } = render(<TimeOfBirthField value="" onChange={onChange} />);
    const native = container.querySelector('input[type="time"]') as HTMLInputElement;

    fireEvent.change(native, { target: { value: "09:15" } });

    expect(onChange).toHaveBeenCalledWith("09:15");
    expect((screen.getByLabelText("Time of birth") as HTMLInputElement).value).not.toBe("");
  });

  it("clears the committed time when the box is emptied", () => {
    const onChange = vi.fn();
    render(<TimeOfBirthField value="14:30" onChange={onChange} />);
    const input = screen.getByLabelText("Time of birth") as HTMLInputElement;

    fireEvent.change(input, { target: { value: "" } });
    fireEvent.blur(input);

    expect(onChange).toHaveBeenCalledWith("");
  });
});
