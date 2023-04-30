import * as React from "react";
import { useState, useEffect } from "react";
import classNames from "classnames";
import ColorPicker from "../ColorPicker/ColorPicker";
import { isString } from "lodash-es";
import "./InputColor.less";

export interface InputColorProps {
	className?: string;
	style?: React.CSSProperties;
	prefixCls?: string;
	width?: number;

	value?: any;
	onChange?: (hex: string) => void;
}

export default function ({
	prefixCls = "solid",
	className,
	style,
	width = 155,
	value = "#000000",
	onChange,
}: InputColorProps) {
	const [displayColorPicker, setDisplayColorPicker] = useState(false);
	const [stateValue, setStateValue] = useState(value);

	useEffect(() => {
		setStateValue(value);
	}, [value]);

	function handleClickColorPicker() {
		setDisplayColorPicker(!displayColorPicker);
	}

	function handleCloseColorPicker() {
		setDisplayColorPicker(false);
	}

	function handleColorChange(color: any) {
		const value = isString(color) ? color : color.hex;
		setStateValue(value);
		onChange && onChange(value);
	}

	function renderColorPicker() {
		if (!displayColorPicker) return undefined;
		return (
			<div className="popover">
				<div
					className="cover"
					onClick={handleCloseColorPicker}
					onKeyPress={handleCloseColorPicker}
					role="button"
					tabIndex={0}
				/>
				<ColorPicker color={stateValue} onChange={handleColorChange} />
			</div>
		);
	}

	let _style: React.CSSProperties = {
		display: "flex",
		justifyContent: "center",
		alignItems: "center",
		width: `${width}px`,
		...style,
	};

	return (
		<div
			className={classNames(prefixCls, "solid-color", className)}
			style={_style}
		>
			<div
				style={{
					backgroundColor: `${stateValue}`,
					width: "100%",
				}}
			>
				<div
					className="swatch"
					onClick={handleClickColorPicker}
					onKeyPress={handleCloseColorPicker}
					role="button"
					tabIndex={0}
				>
					{stateValue}
				</div>

				{renderColorPicker()}
			</div>
		</div>
	);
}
