export class ElevationProfile {

	constructor(lineString, points, maxElevation, minElevation, gain, loss, distance) {
		this.lineString = lineString;
		this.points = points;
		this.maxElevation = maxElevation;
		this.minElevation = minElevation;
		this.gain = gain;
		this.loss = loss;
		this.distance = distance;
		//const elevations = await Promise.all(this.points.map(async (p) => { return await getElevationAt(p.lat, p.lon, 13) }));

	}

	static distance(lat1, lon1, lat2, lon2) {
		const R = 6371000;

		const dLat = (lat2 - lat1) * Math.PI / 180;
		const dLon = (lon2 - lon1) * Math.PI / 180;

		const a =
			Math.sin(dLat / 2) ** 2 +
			Math.cos(lat1 * Math.PI / 180) *
			Math.cos(lat2 * Math.PI / 180) *
			Math.sin(dLon / 2) ** 2;

		return R * 2 * Math.atan2(
			Math.sqrt(a),
			Math.sqrt(1 - a)
		);
	}

	static async create(lineString, map) {

		let cumulative = 0;
		let cumulativeGain = 0;
		let gain = 0;
		let loss = 0;
		let tot_distance = 0;

		const points = lineString.coordinates.map(([lon, lat]) => ({ lon, lat }));
		const result = [];
		const elevations = await Promise.all(
			points.map(p => getElevationAt(p.lon, p.lat, 10, map))
		);
		const coords = elevations.map((ele, index) => [points[index].lon, points[index].lat, ele]);
		console.log("elevations", elevations);
		/*
		(async () => {
			this.elevations = await Promise.all(
				this.points.map(p =>
					getElevationAt(p.lat, p.lon, 13)
				)
			);
		})();
		*/

		for (let i = 1; i < elevations.length; i++) {
			const delta = elevations[i] - elevations[i - 1];

			if (delta > 0) {
				gain += delta;
			} else {
				loss += Math.abs(delta);
			}
		}


		for (let i = 0; i < coords.length; i++) {
			const [lon, lat, eleRaw] = coords[i];

			const ele = eleRaw ?? 0;

			if (i > 0) {
				const [prevLon, prevLat, prevEleRaw] = coords[i - 1];
				const prevEle = prevEleRaw ?? 0;

				cumulative += ElevationProfile.distance(
					prevLat,
					prevLon,
					lat,
					lon
				);

				cumulative + 0;
				const delta = ele - prevEle;

				if (delta > 0) {
					cumulativeGain += delta;
				}
			}
			tot_distance = cumulative;
			result.push({
				distance: cumulative,
				elevation: ele,
				cumulativeGain,
				lon,
				lat
			});
		}
		const maxElevation = Math.max(...elevations);
		const minElevation = Math.min(...elevations);
		gain = cumulativeGain;
		loss = loss;
		//distance = tot_distance;
		console.log("maxElevation", maxElevation);
		console.log("minElevation", minElevation);
		console.log("gain", gain);
		console.log("loss", loss);
		console.log("distance", tot_distance);
		return new ElevationProfile(lineString, result, maxElevation, minElevation, gain, loss, tot_distance);
	}

	stats() {
		return {
			min: this.minElevation,
			max: this.maxElevation,
			gain: Math.round(this.gain),
			loss: Math.round(this.loss),
			distance: this.distance
		};
	}
}
async function getElevationAt(lon, lat, z = 10, map) {
	// Query terrain for elevation
	const elevation = map.queryTerrainElevation([lon, lat], { exaggerated: false }, z = 13);


	//console.log(`Elevation at (${lon.toFixed(5)}, ${lat.toFixed(5)}) for zoom ${map.getZoom()}:`, elevation);
	return elevation !== undefined ? elevation : null;

}

const maplibreApi = globalThis.maplibregl ?? window.maplibregl;

function createMarker(options = {}) {
	if (!maplibreApi?.Marker) {
		return {
			setLngLat() { return this; },
			addTo() { return this; },
			remove() { return this; }
		};
	}

	return new maplibreApi.Marker(options);
}

export function renderElevationProfile(
	container,
	profile,
	width,
	height,
	map
) {
	const margin = {
		top: 10,
		right: 40,
		bottom: 50,
		left: 60
	};

	const chartWidth =
		width - margin.left - margin.right;

	const chartHeight =
		height - margin.top - margin.bottom;

	const elevationRange =
		Math.max(1, profile.maxElevation - profile.minElevation);

	const data = profile.points;
	console.log("data", data);
	console.log("profile", profile);
	const profilePoints = data.map(d => {
		const x =
			margin.left +
			(d.distance / profile.distance) * chartWidth;

		const y =
			margin.top +
			chartHeight -
			((d.elevation - profile.minElevation) / elevationRange)
			* chartHeight;

		return {
			x,
			y,
			...d
		};
	});
	console.log("profilePoints", profilePoints);
	const profileLinePoints = profilePoints
		.map(p => `${p.x},${p.y}`)
		.join(" ");

	const areaPoints = [
		`${margin.left},${margin.top + chartHeight}`,
		...profilePoints.map(p => `${p.x},${p.y}`),
		`${margin.left + chartWidth},${margin.top + chartHeight}`
	].join(" ");

	const yTicks = [];

	for (let i = 0; i <= 5; i++) {
		const value =
			profile.minElevation +
			((profile.maxElevation - profile.minElevation) * i / 5);

		const y =
			margin.top +
			chartHeight -
			(i / 5) * chartHeight;

		yTicks.push({ value, y });
	}

	const xTicks = [];

	for (let i = 0; i <= 5; i++) {
		const distance =
			(profile.distance * i / 5) / 1000;

		const x =
			margin.left +
			(i / 5) * chartWidth;

		xTicks.push({ distance, x });
	}

	container.style.position = "absolute";
	container.style.width = `${width + 30}px`;
	container.style.height = `${height + 10}px`;
	container.style.background = "rgba(255,255,255,0.95)";
	container.style.border = "1px solid #ddd";
	container.style.borderRadius = "8px";
	container.style.boxShadow = "0 2px 8px rgba(0,0,0,0.15)";
	container.style.overflow = "hidden";

	container.innerHTML = `
        <div
            id="elevation-wrapper"
            style="
                position:relative;
                width:${width}px;
            "
        >
            <button
                id="toggle-elevation-profile"
                title="Masquer le profil"
                style="
                    position:absolute;
                    top:6px;
                    right:6px;
                    z-index:20;
                    width:26px;
                    height:26px;
                    border:none;
                    border-radius:50%;
                    background:#ffffff;
                    box-shadow:0 1px 4px rgba(0,0,0,0.25);
                    cursor:pointer;
                    font-size:18px;
                    line-height:24px;
                    font-weight:bold;
                "
            >
                −
            </button>

            <div id="elevation-content">
                <svg
                    id="elevation-svg"
                    width="${width}"
                    height="${height}"
                    viewBox="0 0 ${width} ${height}"
                >
                    <defs>
                        <linearGradient
                            id="elevation-gradient"
                            x1="0"
                            y1="0"
                            x2="0"
                            y2="1"
                        >
                            <stop offset="0%" stop-color="#0f1403" />
                            <stop offset="100%" stop-color="#eaf9ea" />
                        </linearGradient>
                    </defs>

                    <!-- Grille horizontale + labels altitude -->
                    ${yTicks.map(t => `
                        <g>
                            <line
                                x1="${margin.left}"
                                x2="${margin.left + chartWidth}"
                                y1="${t.y}"
                                y2="${t.y}"
                                stroke="#dddddd"
                                stroke-dasharray="2,2"
                            />

                            <line
                                x1="${margin.left - 5}"
                                x2="${margin.left}"
                                y1="${t.y}"
                                y2="${t.y}"
                                stroke="black"
                            />

                            <text
                                x="${margin.left - 10}"
                                y="${t.y + 4}"
                                text-anchor="end"
                                font-size="10"
                                fill="#333"
                            >
                                ${Math.round(t.value)} m
                            </text>
                        </g>
                    `).join("")}

                    <!-- Grille verticale + labels distance -->
                    ${xTicks.map(t => `
                        <g>
                            <line
                                x1="${t.x}"
                                x2="${t.x}"
                                y1="${margin.top}"
                                y2="${margin.top + chartHeight}"
                                stroke="#dddddd"
                                stroke-dasharray="2,2"
                            />

                            <line
                                x1="${t.x}"
                                x2="${t.x}"
                                y1="${margin.top + chartHeight}"
                                y2="${margin.top + chartHeight + 5}"
                                stroke="black"
                            />

                            <text
                                x="${t.x}"
                                y="${margin.top + chartHeight + 18}"
                                text-anchor="middle"
                                font-size="10"
                                fill="#333"
                            >
                                ${t.distance.toFixed(1)} km
                            </text>
                        </g>
                    `).join("")}

                    <!-- Axe Y -->
                    <line
                        x1="${margin.left}"
                        y1="${margin.top}"
                        x2="${margin.left}"
                        y2="${margin.top + chartHeight}"
                        stroke="black"
                    />

                    <!-- Axe X -->
                    <line
                        x1="${margin.left}"
                        y1="${margin.top + chartHeight}"
                        x2="${margin.left + chartWidth}"
                        y2="${margin.top + chartHeight}"
                        stroke="black"
                    />

                    <!-- Surface verte sous la courbe -->
                    <polygon
                        fill="url(#elevation-gradient)"
                        fill-opacity="0.9"
                        points="${areaPoints}"
                    />

                    <!-- Courbe du profil -->
                    <polyline
                        fill="none"
                        stroke="#2ea44b"
                        stroke-width="2"
                        points="${profileLinePoints}"
                    />

                    <!-- Ligne verticale au survol -->
                    <line
                        id="profile-cursor"
                        x1="0"
                        y1="${margin.top}"
                        x2="0"
                        y2="${margin.top + chartHeight}"
                        stroke="red"
                        stroke-width="1"
                        opacity="0"
                    />

                    <!-- Point sur la courbe -->
                    <circle
                        id="profile-point"
                        cx="0"
                        cy="0"
                        r="4"
                        fill="red"
                        opacity="0"
                    />
                </svg>
            </div>

            <div
                id="profile-tooltip"
                style="
                    position:absolute;
                    display:none;
                    pointer-events:none;
                    background:white;
                    border:1px solid #ccc;
                    border-radius:6px;
                    padding:6px 8px;
                    font-size:12px;
                    box-shadow:0 2px 6px rgba(0,0,0,.2);
                    z-index:30;
                    white-space:nowrap;
                "
            ></div>
        </div>
    `;

	const wrapper =
		container.querySelector("#elevation-wrapper");

	const content =
		container.querySelector("#elevation-content");

	const toggleButton =
		container.querySelector("#toggle-elevation-profile");

	const svg =
		container.querySelector("#elevation-svg");

	const cursor =
		container.querySelector("#profile-cursor");

	const pointCircle =
		container.querySelector("#profile-point");

	const tooltip =
		container.querySelector("#profile-tooltip");

	const startMarker = createMarker({ color: "green" });
	const endMarker = createMarker({ color: "red" });
	const hoverMarker = createMarker();

	startMarker.setLngLat({ lng: profile.points[0].lon, lat: profile.points[0].lat }).addTo(map);
	endMarker.setLngLat({ lng: profile.points[profile.points.length - 1].lon, lat: profile.points[profile.points.length - 1].lat }).addTo(map);
	let collapsed = false;

	function clamp(value, min, max) {
		return Math.max(min, Math.min(max, value));
	}

	function findNearestIndexByDistance(targetDistance) {
		let nearestIndex = 0;
		let minDiff = Infinity;

		for (let i = 0; i < data.length; i++) {
			const diff = Math.abs(data[i].distance - targetDistance);

			if (diff < minDiff) {
				minDiff = diff;
				nearestIndex = i;
			}
		}

		return nearestIndex;
	}

	function computeSlope(index) {
		const start =
			Math.max(0, index - 3);

		const end =
			Math.min(data.length - 1, index + 3);

		const p1 = data[start];
		const p2 = data[end];

		const deltaElevation =
			p2.elevation - p1.elevation;

		const deltaDistance =
			p2.distance - p1.distance;

		if (deltaDistance <= 0) {
			return 0;
		}

		return (deltaElevation / deltaDistance) * 100;
	}

	svg.addEventListener("mousemove", e => {
		const rect = svg.getBoundingClientRect();

		const rawMouseX =
			e.clientX - rect.left;

		const mouseY =
			e.clientY - rect.top;

		const mouseX = clamp(
			rawMouseX,
			margin.left,
			margin.left + chartWidth
		);

		const chartX =
			mouseX - margin.left;

		const percentage =
			clamp(chartX / chartWidth, 0, 1);

		const targetDistance =
			percentage * profile.distance;

		const index =
			findNearestIndexByDistance(targetDistance);

		const point =
			data[index];

		if (point.lon !== undefined && point.lat !== undefined) {
			hoverMarker
				.setLngLat([point.lon, point.lat])
				.addTo(map);
		}

		const pointSvg =
			profilePoints[index];

		const slope =
			computeSlope(index);

		const slopeColor =
			slope > 0
				? "#0f9d58"
				: slope < 0
					? "#d93025"
					: "#666";

		// La ligne verticale suit exactement la souris dans la zone utile.
		cursor.setAttribute("x1", mouseX);
		cursor.setAttribute("x2", mouseX);
		cursor.setAttribute("opacity", "1");

		// Le point rouge reste collé au point réel de la courbe.
		pointCircle.setAttribute("cx", pointSvg.x);
		pointCircle.setAttribute("cy", pointSvg.y);
		pointCircle.setAttribute("opacity", "1");

		tooltip.style.display = "block";

		tooltip.innerHTML = `
            <strong>${(point.distance / 1000).toFixed(2)} km</strong><br>
            Altitude : ${Math.round(point.elevation)} m<br>
            D+ cumulé : ${Math.round(point.cumulativeGain)} m<br>
            <span style="color:${slopeColor}">
                Pente : ${slope >= 0 ? "+" : ""}${slope.toFixed(1)} %
            </span>
        `;

		let tooltipLeft = mouseX + 12;
		let tooltipTop = mouseY - 18;

		const tooltipWidth = 130;
		const tooltipHeight = 70;

		if (tooltipLeft + tooltipWidth > width) {
			tooltipLeft = mouseX - tooltipWidth - 12;
		}

		if (tooltipTop < 0) {
			tooltipTop = mouseY + 12;
		}

		if (tooltipTop + tooltipHeight > height) {
			tooltipTop = height - tooltipHeight - 4;
		}

		tooltip.style.left = `${tooltipLeft}px`;
		tooltip.style.top = `${tooltipTop}px`;

		container.dispatchEvent(
			new CustomEvent("profile-hover", {
				detail: point
			})
		);
	});

	svg.addEventListener("mouseleave", () => {
		cursor.setAttribute("opacity", "0");
		pointCircle.setAttribute("opacity", "0");
		tooltip.style.display = "none";
		hoverMarker.remove();
		container.dispatchEvent(
			new CustomEvent("profile-leave")
		);
	});

	toggleButton.addEventListener("click", () => {
		collapsed = !collapsed;

		if (collapsed) {
			content.style.display = "none";
			tooltip.style.display = "none";

			cursor.setAttribute("opacity", "0");
			pointCircle.setAttribute("opacity", "0");

			wrapper.style.height = "38px";
			container.style.height = "38px";

			toggleButton.textContent = "+";
			toggleButton.title = "Afficher le profil";

			container.dispatchEvent(
				new CustomEvent("profile-leave")
			);
		} else {
			content.style.display = "block";

			wrapper.style.height = `${height}px`;
			container.style.height = `${height}px`;

			toggleButton.textContent = "−";
			toggleButton.title = "Masquer le profil";
		}
	});

	wrapper.style.height = `${height}px`;
	container.style.height = `${height}px`;
}