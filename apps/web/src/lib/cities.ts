/**
 * Bundled city table — lat/long/timezone.
 *
 * Why this exists: the engine's `pillars.py` resolves a city name through Nominatim (geopy) at
 * *request* time. That is a network call with a usage policy, real latency, and a silent degrade
 * to "standard time" on failure. Instead, coordinates are resolved ONCE when a profile is created,
 * and the engine always receives explicit values. Engine change E2.
 *
 * See docs/webapp/02-data-model.md §Profile and docs/webapp/05-report-pipeline.md §"Required engine
 * changes".
 *
 * Adding a city: append a row. Use the IANA zone name; the offset is derived at birth time
 * (historical + DST aware) in `birth.ts`.
 */

export interface City {
  name: string;
  country: string;
  countryCode: string;
  latitude: number;
  longitude: number;
  timezone: string;
}

type Row = [name: string, country: string, cc: string, lat: number, lon: number, tz: string];

const ROWS: Row[] = [
  // Korea
  ["Seoul", "South Korea", "KR", 37.5665, 126.978, "Asia/Seoul"],
  ["Busan", "South Korea", "KR", 35.1796, 129.0756, "Asia/Seoul"],
  ["Incheon", "South Korea", "KR", 37.4563, 126.7052, "Asia/Seoul"],
  ["Daegu", "South Korea", "KR", 35.8714, 128.6014, "Asia/Seoul"],
  ["Daejeon", "South Korea", "KR", 36.3504, 127.3845, "Asia/Seoul"],
  ["Gwangju", "South Korea", "KR", 35.1595, 126.8526, "Asia/Seoul"],
  ["Suwon", "South Korea", "KR", 37.2636, 127.0286, "Asia/Seoul"],
  ["Ulsan", "South Korea", "KR", 35.5384, 129.3114, "Asia/Seoul"],
  ["Jeju", "South Korea", "KR", 33.4996, 126.5312, "Asia/Seoul"],

  // Japan
  ["Tokyo", "Japan", "JP", 35.6762, 139.6503, "Asia/Tokyo"],
  ["Yokohama", "Japan", "JP", 35.4437, 139.638, "Asia/Tokyo"],
  ["Osaka", "Japan", "JP", 34.6937, 135.5023, "Asia/Tokyo"],
  ["Kyoto", "Japan", "JP", 35.0116, 135.7681, "Asia/Tokyo"],
  ["Nagoya", "Japan", "JP", 35.1815, 136.9066, "Asia/Tokyo"],
  ["Kobe", "Japan", "JP", 34.6901, 135.1955, "Asia/Tokyo"],
  ["Fukuoka", "Japan", "JP", 33.5904, 130.4017, "Asia/Tokyo"],
  ["Sapporo", "Japan", "JP", 43.0618, 141.3545, "Asia/Tokyo"],

  // China / HK / Taiwan
  ["Beijing", "China", "CN", 39.9042, 116.4074, "Asia/Shanghai"],
  ["Shanghai", "China", "CN", 31.2304, 121.4737, "Asia/Shanghai"],
  ["Guangzhou", "China", "CN", 23.1291, 113.2644, "Asia/Shanghai"],
  ["Shenzhen", "China", "CN", 22.5431, 114.0579, "Asia/Shanghai"],
  ["Chengdu", "China", "CN", 30.5728, 104.0668, "Asia/Shanghai"],
  ["Chongqing", "China", "CN", 29.563, 106.5516, "Asia/Shanghai"],
  ["Xi'an", "China", "CN", 34.3416, 108.9398, "Asia/Shanghai"],
  ["Hangzhou", "China", "CN", 30.2741, 120.1551, "Asia/Shanghai"],
  ["Wuhan", "China", "CN", 30.5928, 114.3055, "Asia/Shanghai"],
  ["Hong Kong", "Hong Kong", "HK", 22.3193, 114.1694, "Asia/Hong_Kong"],
  ["Taipei", "Taiwan", "TW", 25.033, 121.5654, "Asia/Taipei"],
  ["Taichung", "Taiwan", "TW", 24.1477, 120.6736, "Asia/Taipei"],
  ["Kaohsiung", "Taiwan", "TW", 22.6273, 120.3014, "Asia/Taipei"],

  // South-East Asia
  ["Singapore", "Singapore", "SG", 1.3521, 103.8198, "Asia/Singapore"],
  ["Bangkok", "Thailand", "TH", 13.7563, 100.5018, "Asia/Bangkok"],
  ["Chiang Mai", "Thailand", "TH", 18.7883, 98.9853, "Asia/Bangkok"],
  ["Jakarta", "Indonesia", "ID", -6.2088, 106.8456, "Asia/Jakarta"],
  ["Denpasar", "Indonesia", "ID", -8.6705, 115.2126, "Asia/Makassar"],
  ["Surabaya", "Indonesia", "ID", -7.2575, 112.7521, "Asia/Jakarta"],
  ["Manila", "Philippines", "PH", 14.5995, 120.9842, "Asia/Manila"],
  ["Cebu", "Philippines", "PH", 10.3157, 123.8854, "Asia/Manila"],
  ["Hanoi", "Vietnam", "VN", 21.0278, 105.8342, "Asia/Ho_Chi_Minh"],
  ["Ho Chi Minh City", "Vietnam", "VN", 10.8231, 106.6297, "Asia/Ho_Chi_Minh"],
  ["Da Nang", "Vietnam", "VN", 16.0544, 108.2022, "Asia/Ho_Chi_Minh"],
  ["Kuala Lumpur", "Malaysia", "MY", 3.139, 101.6869, "Asia/Kuala_Lumpur"],
  ["Yangon", "Myanmar", "MM", 16.8661, 96.1951, "Asia/Yangon"],
  ["Phnom Penh", "Cambodia", "KH", 11.5564, 104.9282, "Asia/Phnom_Penh"],

  // South Asia
  ["Mumbai", "India", "IN", 19.076, 72.8777, "Asia/Kolkata"],
  ["New Delhi", "India", "IN", 28.6139, 77.209, "Asia/Kolkata"],
  ["Bengaluru", "India", "IN", 12.9716, 77.5946, "Asia/Kolkata"],
  ["Chennai", "India", "IN", 13.0827, 80.2707, "Asia/Kolkata"],
  ["Kolkata", "India", "IN", 22.5726, 88.3639, "Asia/Kolkata"],
  ["Hyderabad", "India", "IN", 17.385, 78.4867, "Asia/Kolkata"],
  ["Pune", "India", "IN", 18.5204, 73.8567, "Asia/Kolkata"],
  ["Ahmedabad", "India", "IN", 23.0225, 72.5714, "Asia/Kolkata"],
  ["Kochi", "India", "IN", 9.9312, 76.2673, "Asia/Kolkata"],
  ["Jaipur", "India", "IN", 26.9124, 75.7873, "Asia/Kolkata"],
  ["Coimbatore", "India", "IN", 11.0168, 76.9558, "Asia/Kolkata"],
  ["Tiruchirappalli", "India", "IN", 10.7905, 78.7047, "Asia/Kolkata"],
  ["Colombo", "Sri Lanka", "LK", 6.9271, 79.8612, "Asia/Colombo"],
  ["Dhaka", "Bangladesh", "BD", 23.8103, 90.4125, "Asia/Dhaka"],
  ["Kathmandu", "Nepal", "NP", 27.7172, 85.324, "Asia/Kathmandu"],
  ["Karachi", "Pakistan", "PK", 24.8607, 67.0011, "Asia/Karachi"],
  ["Lahore", "Pakistan", "PK", 31.5204, 74.3587, "Asia/Karachi"],
  ["Islamabad", "Pakistan", "PK", 33.6844, 73.0479, "Asia/Karachi"],

  // Middle East / Central Asia
  ["Dubai", "United Arab Emirates", "AE", 25.2048, 55.2708, "Asia/Dubai"],
  ["Abu Dhabi", "United Arab Emirates", "AE", 24.4539, 54.3773, "Asia/Dubai"],
  ["Riyadh", "Saudi Arabia", "SA", 24.7136, 46.6753, "Asia/Riyadh"],
  ["Jeddah", "Saudi Arabia", "SA", 21.4858, 39.1925, "Asia/Riyadh"],
  ["Doha", "Qatar", "QA", 25.2854, 51.531, "Asia/Qatar"],
  ["Kuwait City", "Kuwait", "KW", 29.3759, 47.9774, "Asia/Kuwait"],
  ["Tel Aviv", "Israel", "IL", 32.0853, 34.7818, "Asia/Jerusalem"],
  ["Jerusalem", "Israel", "IL", 31.7683, 35.2137, "Asia/Jerusalem"],
  ["Istanbul", "Turkey", "TR", 41.0082, 28.9784, "Europe/Istanbul"],
  ["Ankara", "Turkey", "TR", 39.9334, 32.8597, "Europe/Istanbul"],
  ["Tehran", "Iran", "IR", 35.6892, 51.389, "Asia/Tehran"],
  ["Tashkent", "Uzbekistan", "UZ", 41.2995, 69.2401, "Asia/Tashkent"],

  // Europe
  ["London", "United Kingdom", "GB", 51.5074, -0.1278, "Europe/London"],
  ["Manchester", "United Kingdom", "GB", 53.4808, -2.2426, "Europe/London"],
  ["Birmingham", "United Kingdom", "GB", 52.4862, -1.8904, "Europe/London"],
  ["Glasgow", "United Kingdom", "GB", 55.8642, -4.2518, "Europe/London"],
  ["Dublin", "Ireland", "IE", 53.3498, -6.2603, "Europe/Dublin"],
  ["Paris", "France", "FR", 48.8566, 2.3522, "Europe/Paris"],
  ["Lyon", "France", "FR", 45.764, 4.8357, "Europe/Paris"],
  ["Marseille", "France", "FR", 43.2965, 5.3698, "Europe/Paris"],
  ["Berlin", "Germany", "DE", 52.52, 13.405, "Europe/Berlin"],
  ["Munich", "Germany", "DE", 48.1351, 11.582, "Europe/Berlin"],
  ["Hamburg", "Germany", "DE", 53.5511, 9.9937, "Europe/Berlin"],
  ["Frankfurt", "Germany", "DE", 50.1109, 8.6821, "Europe/Berlin"],
  ["Madrid", "Spain", "ES", 40.4168, -3.7038, "Europe/Madrid"],
  ["Barcelona", "Spain", "ES", 41.3874, 2.1686, "Europe/Madrid"],
  ["Rome", "Italy", "IT", 41.9028, 12.4964, "Europe/Rome"],
  ["Milan", "Italy", "IT", 45.4642, 9.19, "Europe/Rome"],
  ["Amsterdam", "Netherlands", "NL", 52.3676, 4.9041, "Europe/Amsterdam"],
  ["Brussels", "Belgium", "BE", 50.8503, 4.3517, "Europe/Brussels"],
  ["Vienna", "Austria", "AT", 48.2082, 16.3738, "Europe/Vienna"],
  ["Zurich", "Switzerland", "CH", 47.3769, 8.5417, "Europe/Zurich"],
  ["Geneva", "Switzerland", "CH", 46.2044, 6.1432, "Europe/Zurich"],
  ["Stockholm", "Sweden", "SE", 59.3293, 18.0686, "Europe/Stockholm"],
  ["Oslo", "Norway", "NO", 59.9139, 10.7522, "Europe/Oslo"],
  ["Copenhagen", "Denmark", "DK", 55.6761, 12.5683, "Europe/Copenhagen"],
  ["Helsinki", "Finland", "FI", 60.1699, 24.9384, "Europe/Helsinki"],
  ["Warsaw", "Poland", "PL", 52.2297, 21.0122, "Europe/Warsaw"],
  ["Prague", "Czechia", "CZ", 50.0755, 14.4378, "Europe/Prague"],
  ["Budapest", "Hungary", "HU", 47.4979, 19.0402, "Europe/Budapest"],
  ["Bucharest", "Romania", "RO", 44.4268, 26.1025, "Europe/Bucharest"],
  ["Lisbon", "Portugal", "PT", 38.7223, -9.1393, "Europe/Lisbon"],
  ["Athens", "Greece", "GR", 37.9838, 23.7275, "Europe/Athens"],
  ["Moscow", "Russia", "RU", 55.7558, 37.6173, "Europe/Moscow"],
  ["Kyiv", "Ukraine", "UA", 50.4501, 30.5234, "Europe/Kyiv"],

  // Africa
  ["Cairo", "Egypt", "EG", 30.0444, 31.2357, "Africa/Cairo"],
  ["Lagos", "Nigeria", "NG", 6.5244, 3.3792, "Africa/Lagos"],
  ["Abuja", "Nigeria", "NG", 9.0765, 7.3986, "Africa/Lagos"],
  ["Accra", "Ghana", "GH", 5.6037, -0.187, "Africa/Accra"],
  ["Nairobi", "Kenya", "KE", -1.2921, 36.8219, "Africa/Nairobi"],
  ["Johannesburg", "South Africa", "ZA", -26.2041, 28.0473, "Africa/Johannesburg"],
  ["Cape Town", "South Africa", "ZA", -33.9249, 18.4241, "Africa/Johannesburg"],
  ["Casablanca", "Morocco", "MA", 33.5731, -7.5898, "Africa/Casablanca"],
  ["Addis Ababa", "Ethiopia", "ET", 9.032, 38.7469, "Africa/Addis_Ababa"],

  // Americas
  ["New York", "United States", "US", 40.7128, -74.006, "America/New_York"],
  ["Brooklyn", "United States", "US", 40.6782, -73.9442, "America/New_York"],
  ["Boston", "United States", "US", 42.3601, -71.0589, "America/New_York"],
  ["Washington", "United States", "US", 38.9072, -77.0369, "America/New_York"],
  ["Philadelphia", "United States", "US", 39.9526, -75.1652, "America/New_York"],
  ["Atlanta", "United States", "US", 33.749, -84.388, "America/New_York"],
  ["Miami", "United States", "US", 25.7617, -80.1918, "America/New_York"],
  ["Toronto", "Canada", "CA", 43.6532, -79.3832, "America/Toronto"],
  ["Montreal", "Canada", "CA", 45.5017, -73.5673, "America/Toronto"],
  ["Chicago", "United States", "US", 41.8781, -87.6298, "America/Chicago"],
  ["Dallas", "United States", "US", 32.7767, -96.797, "America/Chicago"],
  ["Houston", "United States", "US", 29.7604, -95.3698, "America/Chicago"],
  ["Austin", "United States", "US", 30.2672, -97.7431, "America/Chicago"],
  ["Minneapolis", "United States", "US", 44.9778, -93.265, "America/Chicago"],
  ["Denver", "United States", "US", 39.7392, -104.9903, "America/Denver"],
  ["Phoenix", "United States", "US", 33.4484, -112.074, "America/Phoenix"],
  ["Los Angeles", "United States", "US", 34.0522, -118.2437, "America/Los_Angeles"],
  ["San Francisco", "United States", "US", 37.7749, -122.4194, "America/Los_Angeles"],
  ["San Diego", "United States", "US", 32.7157, -117.1611, "America/Los_Angeles"],
  ["San Jose", "United States", "US", 37.3382, -121.8863, "America/Los_Angeles"],
  ["Seattle", "United States", "US", 47.6062, -122.3321, "America/Los_Angeles"],
  ["Portland", "United States", "US", 45.5152, -122.6784, "America/Los_Angeles"],
  ["Las Vegas", "United States", "US", 36.1699, -115.1398, "America/Los_Angeles"],
  ["Vancouver", "Canada", "CA", 49.2827, -123.1207, "America/Vancouver"],
  ["Mexico City", "Mexico", "MX", 19.4326, -99.1332, "America/Mexico_City"],
  ["Guadalajara", "Mexico", "MX", 20.6597, -103.3496, "America/Mexico_City"],
  ["Bogotá", "Colombia", "CO", 4.711, -74.0721, "America/Bogota"],
  ["Lima", "Peru", "PE", -12.0464, -77.0428, "America/Lima"],
  ["Santiago", "Chile", "CL", -33.4489, -70.6693, "America/Santiago"],
  ["Buenos Aires", "Argentina", "AR", -34.6037, -58.3816, "America/Argentina/Buenos_Aires"],
  ["São Paulo", "Brazil", "BR", -23.5505, -46.6333, "America/Sao_Paulo"],
  ["Rio de Janeiro", "Brazil", "BR", -22.9068, -43.1729, "America/Sao_Paulo"],
  ["Honolulu", "United States", "US", 21.3069, -157.8583, "Pacific/Honolulu"],

  // Oceania
  ["Sydney", "Australia", "AU", -33.8688, 151.2093, "Australia/Sydney"],
  ["Melbourne", "Australia", "AU", -37.8136, 144.9631, "Australia/Melbourne"],
  ["Brisbane", "Australia", "AU", -27.4698, 153.0251, "Australia/Brisbane"],
  ["Perth", "Australia", "AU", -31.9505, 115.8605, "Australia/Perth"],
  ["Adelaide", "Australia", "AU", -34.9285, 138.6007, "Australia/Adelaide"],
  ["Auckland", "New Zealand", "NZ", -36.8485, 174.7633, "Pacific/Auckland"],
  ["Wellington", "New Zealand", "NZ", -41.2865, 174.7762, "Pacific/Auckland"],
];

export const CITIES: City[] = ROWS.map(([name, country, countryCode, latitude, longitude, timezone]) => ({
  name,
  country,
  countryCode,
  latitude,
  longitude,
  timezone,
}));

const norm = (s: string) => s.trim().toLowerCase();

export function findCity(name: string, countryCode?: string | null): City | null {
  const target = norm(name);
  const cc = countryCode ? norm(countryCode) : null;
  const pool = cc ? CITIES.filter((c) => norm(c.countryCode) === cc) : CITIES;
  return (
    pool.find((c) => norm(c.name) === target) ??
    CITIES.find((c) => norm(c.name) === target) ??
    null
  );
}

/** Prefix/substring search for the typeahead. Deterministic ordering, no network. */
export function searchCities(query: string, limit = 8): City[] {
  const q = norm(query);
  if (q.length < 1) return [];
  const scored = CITIES.map((c) => {
    const name = norm(c.name);
    const country = norm(c.country);
    let score = -1;
    if (name.startsWith(q)) score = 0;
    else if (name.includes(q)) score = 1;
    else if (country.startsWith(q)) score = 2;
    else if (`${name}, ${country}`.includes(q)) score = 3;
    return { c, score };
  })
    .filter((s) => s.score >= 0)
    .sort((a, b) => a.score - b.score || a.c.name.localeCompare(b.c.name));
  return scored.slice(0, limit).map((s) => s.c);
}

export function listCountries(): { country: string; countryCode: string }[] {
  const seen = new Map<string, string>();
  for (const c of CITIES) if (!seen.has(c.country)) seen.set(c.country, c.countryCode);
  return [...seen.entries()]
    .map(([country, countryCode]) => ({ country, countryCode }))
    .sort((a, b) => a.country.localeCompare(b.country));
}

export function formatCityLabel(c: City): string {
  return `${c.name}, ${c.country}`;
}
