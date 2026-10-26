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

  /**
   * AU-16 (2026-10-26 audit): clearing or mistyping the field left the *previous* value in the
   * parent's state, so the form submitted a date the visitor no longer saw. Both paths now emit
   * `""`, and a parse error makes the control invalid so the browser refuses to submit the form.
   */
  it("emits an empty value when the field is cleared, rather than keeping the old date", () => {
    const onChange = vi.fn();
    render(<DateOfBirthField value="1993-03-19" onChange={onChange} />);
    const input = screen.getByLabelText("Date of birth") as HTMLInputElement;

    // No blur: a click before blur must still not submit the date that is no longer on screen.
    fireEvent.change(input, { target: { value: "" } });

    expect(onChange).toHaveBeenCalledWith("");
  });

  it("emits an empty value for a partial date and blocks form submission", () => {
    const onChange = vi.fn();
    const { container } = render(
      <form>
        <DateOfBirthField value="1993-03-19" onChange={onChange} />
      </form>,
    );
    const input = screen.getByLabelText("Date of birth") as HTMLInputElement;

    fireEvent.change(input, { target: { value: "19/03" } });
    fireEvent.blur(input);

    expect(onChange).toHaveBeenCalledWith("");
    expect(screen.getByText(/Use YYYY-MM-DD/)).toBeTruthy();
    expect(input.validationMessage).toMatch(/Use YYYY-MM-DD/);
    expect(container.querySelector("form")!.checkValidity()).toBe(false);
  });

  it("clears the parse error once the date is understood again", () => {
    const onChange = vi.fn();
    const { container } = render(
      <form>
        <DateOfBirthField value="1993-03-19" onChange={onChange} />
      </form>,
    );
    const input = screen.getByLabelText("Date of birth") as HTMLInputElement;

    fireEvent.change(input, { target: { value: "19/03" } });
    fireEvent.blur(input);
    expect(container.querySelector("form")!.checkValidity()).toBe(false);

    fireEvent.change(input, { target: { value: "19/03/1993" } });
    fireEvent.blur(input);

    expect(onChange).toHaveBeenLastCalledWith("1993-03-19");
    expect(input.validationMessage).toBe("");
    expect(container.querySelector("form")!.checkValidity()).toBe(true);
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

  it("emits an empty value when the field is cleared, rather than keeping the old time", () => {
    const onChange = vi.fn();
    render(<TimeOfBirthField value="14:30" onChange={onChange} />);
    const input = screen.getByLabelText("Time of birth") as HTMLInputElement;

    // No blur: a click before blur must still not submit the time that is no longer on screen.
    fireEvent.change(input, { target: { value: "" } });

    expect(onChange).toHaveBeenCalledWith("");
  });

  it("emits an empty value for a partial time and blocks form submission", () => {
    const onChange = vi.fn();
    const { container } = render(
      <form>
        <TimeOfBirthField value="14:30" onChange={onChange} />
      </form>,
    );
    const input = screen.getByLabelText("Time of birth") as HTMLInputElement;

    fireEvent.change(input, { target: { value: "2:" } });
    fireEvent.blur(input);

    expect(onChange).toHaveBeenCalledWith("");
    expect(screen.getByText(/Use a 24-hour time/)).toBeTruthy();
    expect(input.validationMessage).toMatch(/Use a 24-hour time/);
    expect(container.querySelector("form")!.checkValidity()).toBe(false);
  });
});
