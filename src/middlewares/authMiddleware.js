import jwt from "jsonwebtoken";
import { JWT_SECRET } from "../config/dotenv.js";

export const authenticateToken = (req, res, next) => {
    const token = req.headers.authorization?.split(" ")[1]; // Expecting "Bearer <token>"

    if (!token) {
        return res.status(401).json({ message: "Access denied. No token provided." });
    }

    try {
        const decoded = jwt.verify(token, JWT_SECRET);
        req.user = decoded; // Add user info to the request object
        next();
    } catch (error) {
        res.status(403).json({ message: "Invalid or expired token." });
    }
};
