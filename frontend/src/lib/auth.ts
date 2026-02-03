import { betterAuth } from "better-auth";
import { jwt } from "better-auth/plugins";
import { Pool } from "pg";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

export const auth = betterAuth({
  database: pool,
  plugins: [jwt({
    jwks: {
      keyPairConfig: {
        alg: "RS256",
      },
    },
  })],
  emailAndPassword: {
    enabled: true,
  },
});
